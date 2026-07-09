"""
VeriDoc — central configuration.
Change settings here; the rest of the code reads from this file.
"""
import os
from pathlib import Path

# Loading a local .env file is optional. On cloud hosting (Streamlit Cloud)
# there is no .env and python-dotenv may not be installed — that's fine,
# because secrets are provided as environment variables instead.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Paths ---
BASE_DIR = Path(__file__).parent
DOCUMENTS_DIR = BASE_DIR / "documents"      # put your college files here
CHROMA_DIR = BASE_DIR / "chroma_db"          # vector store lives here
COLLECTION_NAME = "veridoc"

# --- Chunking ---
CHUNK_SIZE = 800        # characters per passage
CHUNK_OVERLAP = 150     # overlap so sentences aren't cut mid-thought

# --- Embeddings (runs locally, free) ---
EMBED_MODEL = "all-MiniLM-L6-v2"   # try "BAAI/bge-small-en-v1.5" for better quality

# --- Retrieval ---
TOP_K = 5               # passages retrieved per question
# Re-ranking improves accuracy but uses more memory. On free cloud hosting
# (limited RAM) set the env var USE_RERANK=false to turn it off.
USE_RERANK = os.getenv("USE_RERANK", "true").lower() == "true"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# The retrieval score below which we treat the question as "not answerable".
# Tune this in Phase 4 using your benchmark — it controls honest refusal.
MIN_RELEVANCE = 0.15

# --- LLM ---
# "ollama"  -> free, offline local (install Ollama + `ollama pull llama3`)
# "gemini"  -> free API, works on cloud (needs GEMINI_API_KEY)
# "openai"  -> paid API (needs OPENAI_API_KEY)
# The env var LLM_MODE overrides this, so the cloud can set it via Secrets
# without changing code. Locally it stays "ollama".
LLM_MODE = os.getenv("LLM_MODE", "ollama")

OLLAMA_MODEL = "llama3"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
