"""
Phase 4 — Grounded answer generation.

This is the core contribution of VeriDoc:
  * answer ONLY from retrieved passages
  * always cite the source
  * refuse honestly when the answer is not in the documents

The refusal has TWO layers of protection:
  1. A relevance gate: if the best passage scores below MIN_RELEVANCE,
     we refuse before even calling the LLM.
  2. A strict prompt that instructs the model to refuse if the answer
     isn't in the provided context.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import config
from retriever import retrieve, Passage

REFUSAL = "I could not find this information in the official documents."

SYSTEM_PROMPT = """You are VeriDoc, an assistant that answers questions about \
an educational institution using ONLY the provided context passages.

Rules you MUST follow:
1. Answer strictly from the context below. Never use outside knowledge.
2. If the answer is not clearly stated in the context, reply with EXACTLY:
   "I could not find this information in the official documents."
3. Be concise and factual. Do not guess or add caveats.
4. After your answer, do not invent sources — the system adds citations.

Context passages:
{context}

Question: {question}

Answer:"""


@dataclass
class Answer:
    text: str
    passages: list[Passage] = field(default_factory=list)
    refused: bool = False


# ------------------------------------------------------------- LLM backends
def _call_ollama(prompt: str) -> str:
    import urllib.request, json
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},   # deterministic, less hallucination
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["response"].strip()


def _call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    """Google Gemini — free API tier, used for cloud deployment."""
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": 0.0},
    )
    return resp.text.strip()


def _call_llm(prompt: str) -> str:
    if config.LLM_MODE == "openai":
        return _call_openai(prompt)
    if config.LLM_MODE == "gemini":
        return _call_gemini(prompt)
    return _call_ollama(prompt)


# ------------------------------------------------------------- main entry
def format_citation(p: Passage) -> str:
    loc = f", page {p.page}" if p.page else ""
    return f"{p.source}{loc}"


def ask(question: str) -> Answer:
    """Retrieve, gate on relevance, then generate a grounded answer."""
    passages = retrieve(question)

    # Layer 1 — relevance gate (honest refusal without calling the LLM).
    if not passages or passages[0].score < config.MIN_RELEVANCE:
        return Answer(text=REFUSAL, passages=[], refused=True)

    context = "\n\n".join(
        f"[Source: {format_citation(p)}]\n{p.text}" for p in passages
    )
    prompt = SYSTEM_PROMPT.format(context=context, question=question)

    try:
        raw = _call_llm(prompt)
    except Exception as e:
        return Answer(text=f"[LLM error: {e}]", passages=passages, refused=False)

    # Layer 2 — detect a model refusal so the UI can hide citations.
    refused = REFUSAL.lower()[:30] in raw.lower()
    return Answer(text=raw, passages=[] if refused else passages, refused=refused)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is the last date to pay the semester fee?"
    a = ask(q)
    print("Q:", q)
    print("A:", a.text)
    if a.passages:
        print("\nSources:")
        for p in a.passages:
            print(" -", format_citation(p))
