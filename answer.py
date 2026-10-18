from __future__ import annotations
import re
import threading
from dataclasses import dataclass, field

import config
from retriever import retrieve, Passage

REFUSAL = "I could not find this information in the official documents."

_REFUSAL_PATTERNS = [
    # English
    r"could not find this information",
    r"could not find",
    r"not found in (the )?official documents",
    r"not found in",
    r"does not contain",
    r"no information .*official documents",
    # Hindi
    r"जानकारी नहीं मिली",
    r"दस्तावेज़ों में.*नहीं",
    r"दस्तावेजों में.*नहीं",
    r"आधिकारिक दस्तावेज़.*नहीं",
    r"आधिकारिक दस्तावेज.*नहीं",
    r"उपलब्ध नहीं है",
    # Marathi
    r"माहिती आढळली नाही",
    r"माहिती सापडली नाही",
    r"कागदपत्रां.*नाही",
    r"अधिकृत कागदपत्र.*नाही",
]
_REFUSAL_REGEX = re.compile("|".join(_REFUSAL_PATTERNS), re.IGNORECASE)


def is_refusal(text: str) -> bool:
    """Check whether the model text represents an honest refusal in English, Hindi, or Marathi."""
    if not text:
        return False
    t = text.strip()
    if REFUSAL.lower()[:30] in t.lower():
        return True
    return bool(_REFUSAL_REGEX.search(t))

SYSTEM_PROMPT = """You are VeriDoc, an assistant that answers questions about \
an educational institution using ONLY the provided context passages.

Rules you MUST follow:
1. Answer strictly from the context below. Never use outside knowledge.
2. If the answer is not clearly stated in the context, reply with EXACTLY this
   English sentence (do not translate it):
   "I could not find this information in the official documents."
3. {detail} Do not guess or add unsupported caveats.
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
    is_error: bool = False
    error_message: str | None = None


def _call_ollama(prompt: str) -> str:
    import urllib.request, json
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }
    base_url = getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["response"].strip()


_openai_client = None
_openai_lock = threading.Lock()


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        with _openai_lock:
            if _openai_client is None:
                from openai import OpenAI
                _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client


def _call_openai(prompt: str) -> str:
    client = _get_openai_client()
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL, temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    content = resp.choices[0].message.content
    return content.strip() if content else ""


_gemini_model_name = None
_gemini_lock = threading.Lock()
_gemini_configured = False


def _call_gemini(prompt: str) -> str:
    global _gemini_model_name, _gemini_configured
    import google.generativeai as genai

    with _gemini_lock:
        if not _gemini_configured:
            genai.configure(api_key=config.GEMINI_API_KEY)
            _gemini_configured = True

    def run(name):
        model = genai.GenerativeModel(name)
        resp = model.generate_content(
            prompt, generation_config={"temperature": 0.0})
        if not resp.candidates:
            raise ValueError(f"Gemini returned no candidates for model {name}")
        candidate = resp.candidates[0]
        if hasattr(candidate, "finish_reason") and candidate.finish_reason == 3:
            return REFUSAL
        try:
            return resp.text.strip()
        except (ValueError, AttributeError) as e:
            if candidate.content and candidate.content.parts:
                parts_text = "".join(p.text for p in candidate.content.parts if hasattr(p, "text"))
                if parts_text:
                    return parts_text.strip()
            raise ValueError(f"Unable to extract text from Gemini response: {e}") from e

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


def format_citation(p: Passage) -> str:
    loc = f", page {p.page}" if p.page else ""
    return f"{p.source}{loc}"


def ask(question: str, language: str = "English", simplify: bool = False,
        detail: str = "Concise",
        allowed_sources: set[str] | None = None) -> Answer:
    passages = retrieve(question, allowed_sources=allowed_sources)

    if not passages or passages[0].score < config.MIN_RELEVANCE:
        return Answer(text=REFUSAL, passages=[], refused=True)

    context = "\n\n".join(
        f"[Source: {format_citation(p)}]\n{p.text}" for p in passages
    )
    style = ("\n6. Explain in very simple, easy words that a first-year student "
             "with no background can understand.") if simplify else ""
    detail_rule = ("Give a structured answer with the relevant conditions and steps."
                   if detail == "Detailed" else "Be concise and factual.")
    prompt = SYSTEM_PROMPT.format(context=context, question=question,
                                  language=language, style=style, detail=detail_rule)

    try:
        raw = _call_llm(prompt)
    except Exception as e:
        return Answer(
            text="An error occurred while generating the answer. Please try again.",
            passages=[],
            refused=False,
            is_error=True,
            error_message=str(e),
        )

    refused = is_refusal(raw)
    return Answer(
        text=raw,
        passages=[] if refused else passages,
        refused=refused,
        is_error=False,
        error_message=None,
    )


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
