"""
Phase 3 (part 2) — Retrieval + optional re-ranking.

Given a question, return the most relevant passages along with a
relevance score used later to decide whether to answer or refuse.
"""
from __future__ import annotations
from dataclasses import dataclass

import config
from index_store import get_embedder, get_collection

_reranker = None


@dataclass
class Passage:
    text: str
    source: str
    page: int
    score: float     # higher = more relevant


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print(f"Loading re-ranker: {config.RERANK_MODEL}")
        _reranker = CrossEncoder(config.RERANK_MODEL)
    return _reranker


def retrieve(question: str, top_k: int | None = None) -> list[Passage]:
    """Return top passages for a question, best first."""
    top_k = top_k or config.TOP_K
    embedder = get_embedder()
    collection = get_collection()

    if collection.count() == 0:
        raise RuntimeError("Index is empty. Run `python index_store.py` first.")

    # Over-fetch, then re-rank down to top_k for better precision.
    fetch_n = top_k * 4 if config.USE_RERANK else top_k
    q_vec = embedder.encode([question], normalize_embeddings=True)[0].tolist()
    res = collection.query(query_embeddings=[q_vec], n_results=fetch_n)

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    distances = res["distances"][0]           # cosine distance (0 = identical)

    passages = []
    for text, meta, dist in zip(docs, metas, distances):
        passages.append(Passage(
            text=text,
            source=meta.get("source", "unknown"),
            page=meta.get("page", 0),
            score=1.0 - dist,                  # convert distance -> similarity
        ))

    if config.USE_RERANK and passages:
        reranker = _get_reranker()
        pairs = [(question, p.text) for p in passages]
        scores = reranker.predict(pairs)
        for p, s in zip(passages, scores):
            p.score = float(s)
        passages.sort(key=lambda p: p.score, reverse=True)
        # cross-encoder scores are unbounded; squash to 0..1 for the threshold
        for p in passages:
            p.score = 1 / (1 + pow(2.718281828, -p.score))

    passages.sort(key=lambda p: p.score, reverse=True)
    return passages[:top_k]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is the last date to pay the fee?"
    for p in retrieve(q):
        print(f"[{p.score:.2f}] {p.source} p{p.page}: {p.text[:120]}...")
