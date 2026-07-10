"""
Phase 4 — Grounded answer generation.

Core contribution of VeriDoc:
  * answer ONLY from retrieved passages
  * always cite the source
  * refuse honestly when the answer is not in the documents
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
2. If the answer is not clearly stated in the context, reply with EXACTLY this
   English sentence (do not translate it):
   "I could not find this information in the official documents."
3. Be concise and factual. Do not guess or add caveats.
4. Do not invent sources — the system adds citations.
5. If the answer IS found, write it in {language}.{style}

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
        "options": {"temperature": 0.0},
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
        model=config.OPENAI_MODEL, temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# Remember the first Gemini model that works, so we don't re-probe every call.
_gemini_model_name = None


def _call_gemini(prompt: str) -> str:
    """Google Gemini. Model names change over time, so we try several known
    names and, if all fail, ask the API which models support generateContent."""
    global _gemini_model_name
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)

    def run(name):
        return genai.GenerativeModel(name).generate_content(
            prompt, generation_config={"temperature": 0.0}).text.strip()

    if _gemini_model_name:
        return run(_gemini_model_name)

    candidates = [config.GEMINI_MODEL, "gemini-2.0-flash", "gemini-2.5-flash",
                  "gemini-flash-latest", "gemini-1.5-flash-latest"]
    errors = []
    for name in candidates:
        if not name:
            continue
        try:
            out = run(name)
            _gemini_model_name = name
            return out
        except Exception as e:
            errors.append(f"{name}: {str(e)[:50]}")

    # Last resort: discover a supported model from the API.
    try:
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                try:
                    out = run(m.name)
                    _gemini_model_name = m.name
                    return out
                except Exception:
                    continue
    except Exception as e:
        errors.append(f"list_models: {str(e)[:50]}")

    raise RuntimeError("No working Gemini model found. Tried: " + " | ".join(errors))


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


def ask(question: str, language: str = "English", simplify: bool = False) -> Answer:
    """Retrieve, gate on relevance, then generate a grounded answer.

    language  — language of the answer (English / Hindi / Hinglish).
    simplify  — if True, explain in very simple, beginner-friendly words.
    """
    passages = retrieve(question)

    if not passages or passages[0].score < config.MIN_RELEVANCE:
        return Answer(text=REFUSAL, passages=[], refused=True)

    context = "\n\n".join(
        f"[Source: {format_citation(p)}]\n{p.text}" for p in passages
    )
    style = ("\n6. Explain in very simple, easy words that a first-year student "
             "with no background can understand.") if simplify else ""
    prompt = SYSTEM_PROMPT.format(context=context, question=question,
                                  language=language, style=style)

    try:
        raw = _call_llm(prompt)
    except Exception as e:
        return Answer(text=f"[LLM error: {e}]", passages=passages, refused=False)

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
