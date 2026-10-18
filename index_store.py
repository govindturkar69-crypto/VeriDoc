from __future__ import annotations
import json
import os
import pickle
import threading
from pathlib import Path

import numpy as np

import config
from ingest import load_documents

STORE_NPZ_PATH = config.CHROMA_DIR / "store_vectors.npz"
STORE_META_PATH = config.CHROMA_DIR / "store_meta.json"
STORE_LEGACY_PATH = config.CHROMA_DIR / "store.pkl"

_embedder = None
_store = None
_store_lock = threading.Lock()
_embedder_lock = threading.Lock()


def get_embedder() -> "SentenceTransformer":
    """Lazily import and instantiate the SentenceTransformer model in a thread-safe manner."""
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as e:
                    raise ImportError(
                        "The 'sentence-transformers' package is required for embedding functionality. "
                        "Install it via `pip install sentence-transformers`."
                    ) from e
                print(f"Loading embedding model: {config.EMBED_MODEL}")
                _embedder = SentenceTransformer(config.EMBED_MODEL)
    return _embedder


def _save_store_files(store: dict) -> None:
    """Safely persist vector array and metadata using npz and json."""
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    temp_npz = config.CHROMA_DIR / "store_vectors.tmp.npz"
    np.savez_compressed(temp_npz, vectors=store["vectors"])
    if temp_npz.exists():
        temp_npz.replace(STORE_NPZ_PATH)

    meta = {
        "ids": store["ids"],
        "texts": store["texts"],
        "sources": store["sources"],
        "pages": store["pages"],
    }
    temp_meta = config.CHROMA_DIR / "store_meta.tmp.json"
    with open(temp_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    if temp_meta.exists():
        temp_meta.replace(STORE_META_PATH)


def load_store() -> dict:
    """Thread-safe loading of vector store with automatic migration from legacy pickle."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                # 1. Try loading safe NPZ + JSON format
                if STORE_NPZ_PATH.exists() and STORE_META_PATH.exists():
                    try:
                        with np.load(STORE_NPZ_PATH) as data:
                            vectors = data["vectors"]
                        with open(STORE_META_PATH, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        _store = {
                            "ids": meta.get("ids", []),
                            "texts": meta.get("texts", []),
                            "sources": meta.get("sources", []),
                            "pages": meta.get("pages", []),
                            "vectors": vectors,
                        }
                    except Exception as e:
                        print(f"Warning: Failed to load store from npz/json ({e}).")

                # 2. Backwards compatibility: load legacy store.pkl once and auto-migrate
                if _store is None and STORE_LEGACY_PATH.exists():
                    try:
                        print("Migrating legacy pickle vector store to safe npz/json format...")
                        with open(STORE_LEGACY_PATH, "rb") as f:
                            _store = pickle.load(f)
                        _save_store_files(_store)
                        print("Migration complete. Vector store saved to npz/json format.")
                    except Exception as e:
                        print(f"Warning: Failed to migrate legacy pickle store: {e}")

                # 3. Default empty store
                if _store is None:
                    _store = {
                        "ids": [],
                        "texts": [],
                        "sources": [],
                        "pages": [],
                        "vectors": np.zeros((0, 384), dtype=np.float32),
                    }
    return _store


def count() -> int:
    return len(load_store()["ids"])


def build_index() -> None:
    global _store
    chunks = load_documents()
    if not chunks:
        return

    embedder = get_embedder()
    texts = [c.text for c in chunks]
    print(f"Embedding {len(texts)} chunks ...")
    vectors = embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    vectors = np.asarray(vectors, dtype=np.float32)

    new_store = {
        "ids": [c.chunk_id for c in chunks],
        "texts": texts,
        "sources": [c.source for c in chunks],
        "pages": [c.page for c in chunks],
        "vectors": vectors,
    }

    with _store_lock:
        _save_store_files(new_store)
        _store = new_store

    print(f"\nIndex built: {len(texts)} chunks stored in {STORE_NPZ_PATH} and {STORE_META_PATH}")


if __name__ == "__main__":
    build_index()

