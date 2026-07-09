"""
Phase 3 (part 1) — Build the search index.

Embeds every chunk and stores it in a local ChromaDB collection.
Run this whenever you add or change documents:

    python index_store.py
"""
from __future__ import annotations
import shutil

import chromadb
from sentence_transformers import SentenceTransformer

import config
from ingest import load_documents


_embedder = None


def get_embedder() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    global _embedder
    if _embedder is None:
        print(f"Loading embedding model: {config.EMBED_MODEL}")
        _embedder = SentenceTransformer(config.EMBED_MODEL)
    return _embedder


def get_collection(reset: bool = False):
    """Return the ChromaDB collection (optionally wiped first)."""
    if reset and config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index() -> None:
    """Full rebuild: load docs, embed, store."""
    chunks = load_documents()
    if not chunks:
        return

    embedder = get_embedder()
    collection = get_collection(reset=True)

    texts = [c.text for c in chunks]
    print(f"Embedding {len(texts)} chunks ...")
    vectors = embedder.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    collection.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=[v.tolist() for v in vectors],
        documents=texts,
        metadatas=[{"source": c.source, "page": c.page} for c in chunks],
    )
    print(f"\nIndex built: {collection.count()} chunks stored in {config.CHROMA_DIR}")


if __name__ == "__main__":
    build_index()
