"""
Two baseline systems to compare against VeriDoc (for Phase 6).

  1. keyword_answer  — a plain keyword-search baseline. It scores each
     document chunk by word overlap with the question and returns the best
     chunk as the "answer". It has NO grounding and CANNOT refuse — it always
     returns something, even for questions the documents don't cover. This
     shows why keyword search is not trustworthy.

  2. vanilla_answer  — a normal chatbot baseline. It sends the question
     straight to the LLM with NO retrieved context. For college-specific
     facts it will hallucinate (make up) answers, because it has no access
     to the official documents.

Place this file in  veridoc/evaluation/  next to evaluate.py.
"""
from __future__ import annotations
import re
import sys
import math
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
import config                       # noqa: E402
from ingest import load_documents   # noqa: E402
from answer import _call_llm        # noqa: E402

_STOP = set("a an the is are was were of to in on at for and or with from by "
            "what when how much many is do does can i my the a it as be this "
            "that will would should which who whom where why".split())


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP]


# ----------------------------------------------------------- keyword baseline
class _KeywordIndex:
    """Tiny TF-IDF-style keyword search over the same document chunks."""
    def __init__(self):
        self.chunks = load_documents()
        self.docs = [_tokens(c.text) for c in self.chunks]
        # document frequency for idf
        df = Counter()
        for toks in self.docs:
            for w in set(toks):
                df[w] += 1
        n = max(len(self.docs), 1)
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}

    def search(self, question: str):
        q = _tokens(question)
        best_score, best = 0.0, None
        for chunk, toks in zip(self.chunks, self.docs):
            tf = Counter(toks)
            score = sum(tf[w] * self.idf.get(w, 0) for w in q)
            if score > best_score:
                best_score, best = score, chunk
        return best, best_score


_kw_index: _KeywordIndex | None = None


def keyword_answer(question: str) -> str:
    """Always returns the best-matching passage — never refuses."""
    global _kw_index
    if _kw_index is None:
        _kw_index = _KeywordIndex()
    chunk, score = _kw_index.search(question)
    if chunk is None:
        return "(no document text available)"
    # A keyword system just hands back raw text; it cannot say "not found".
    return chunk.text[:280]


# ----------------------------------------------------------- vanilla chatbot
def vanilla_answer(question: str) -> str:
    """Sends the question directly to the LLM with no document context."""
    prompt = (
        "You are a helpful assistant answering a student's question about "
        "their college. Answer directly and concisely.\n\n"
        f"Question: {question}\nAnswer:"
    )
    try:
        return _call_llm(prompt).strip()
    except Exception as e:
        return f"[LLM error: {e}]"


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the last date to pay the fee?"
    print("Q:", q)
    print("\n[keyword baseline]\n", keyword_answer(q))
    print("\n[vanilla chatbot]\n", vanilla_answer(q))
