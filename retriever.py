from __future__ import annotations
from dataclasses import dataclass

import numpy as np

import config
from index_store import get_embedder, load_store

_reranker = None


@dataclass
class Passage:
    text: str
    source: str
    page: int
    score: float


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print(f"Loading re-ranker: {config.RERANK_MODEL}")
        _reranker = CrossEncoder(config.RERANK_MODEL)
    return _reranker


def retrieve(question: str, top_k: int | None = None) -> list[Passage]:
    top_k = top_k or config.TOP_K
    store = load_store()

    if len(store["ids"]) == 0:
        raise RuntimeError("Index is empty. Run `python index_store.py` first.")

    fetch_n = top_k * 4 if config.USE_RERANK else top_k

    q_vec = get_embedder().encode([question], normalize_embeddings=True)[0].astype(np.float32)
    sims = store["vectors"] @ q_vec
    order = np.argsort(-sims)[:fetch_n]

    passages = [
        Passage(
            text=store["texts"][i],
            source=store["sources"][i],
            page=store["pages"][i],
            score=float(sims[i]),
        )
        for i in order
    ]

    if config.USE_RERANK and passages:
        reranker = _get_reranker()
        scores = reranker.predict([(question, p.text) for p in passages])
        for p, s in zip(passages, scores):
            p.score = 1 / (1 + np.exp(-float(s)))
        passages.sort(key=lambda p: p.score, reverse=True)

    passages.sort(key=lambda p: p.score, reverse=True)
    return passages[:top_k]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is the last date to pay the fee?"
    for p in retrieve(q):
        print(f"[{p.score:.2f}] {p.source} p{p.page}: {p.text[:120]}...")
