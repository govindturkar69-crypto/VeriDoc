"""
Phase 3 (part 1) — Build the search index.

Uses a lightweight in-memory vector store (NumPy) instead of a heavy native
database. For a small document set this is fast, uses little memory, and works
everywhere (local + cloud, any Python version). The index is embedded and saved
to a single pickle file so it can be reused without rebuilding.

Run this whenever you add or change documents:
    python index_store.py
"""
from __future__ import annotations
import pickle

import numpy as np
from sentence_transformers import SentenceTransformer

import config
from ingest import load_documents

STORE_PATH = config.CHROMA_DIR / "store.pkl"

_embedder = None
_store = None


def get_embedder() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    global _embedder
    if _embedder is None:
        print(f"Loading embedding model: {config.EMBED_MODEL}")
        _embedder = SentenceTransformer(config.EMBED_MODEL)
    return _embedder


def load_store() -> dict:
    """Load the saved index into memory (or return an empty one)."""
    global _store
    if _store is None:
        if STORE_PATH.exists():
            with open(STORE_PATH, "rb") as f:
                _store = pickle.load(f)
        else:
            _store = {"ids": [], "texts": [], "sources": [], "pages": [],
                      "vectors": np.zeros((0, 384), dtype=np.float32)}
    return _store


def count() -> int:
    return len(load_store()["ids"])


def build_index() -> None:
    """Full rebuild: load docs, embed, store."""
    global _store
    chunks = load_documents()
    if not chunks:
        return

    embedder = get_embedder()
    texts = [c.text for c in chunks]
    print(f"Embedding {len(texts)} chunks ...")
    vectors = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    vectors = np.asarray(vectors, dtype=np.float32)

    _store = {
        "ids": [c.chunk_id for c in chunks],
        "texts": texts,
        "sources": [c.source for c in chunks],
        "pages": [c.page for c in chunks],
        "vectors": vectors,
    }

    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "wb") as f:
        pickle.dump(_store, f)
    print(f"\nIndex built: {len(texts)} chunks stored in {STORE_PATH}")


if __name__ == "__main__":
    build_index()
