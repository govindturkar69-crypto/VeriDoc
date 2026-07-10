"""
VeriDoc — central configuration.
Change settings here; the rest of the code reads from this file.
"""
import os
from pathlib import Path

# Loading a local .env file is optional. On cloud hosting there is no .env and
# python-dotenv may not be installed — that's fine, secrets come as env vars.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Paths ---
BASE_DIR = Path(__file__).parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "veridoc"

# --- Chunking ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# --- Embeddings (runs locally, free) ---
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- Retrieval ---
TOP_K = 5
USE_RERANK = os.getenv("USE_RERANK", "true").lower() == "true"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MIN_RELEVANCE = 0.15

# --- LLM ---
# "ollama"  -> free, offline local (install Ollama + `ollama pull llama3`)
# "gemini"  -> free API, works on cloud (needs GEMINI_API_KEY)
# "openai"  -> paid API (needs OPENAI_API_KEY)
LLM_MODE = os.getenv("LLM_MODE", "ollama")

OLLAMA_MODEL = "llama3"

# gemini-2.5-flash is a current, widely-available model. (gemini-1.5-flash was
# retired.) You can override this with the GEMINI_MODEL env var / secret.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
