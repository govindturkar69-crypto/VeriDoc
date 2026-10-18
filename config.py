import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

EMBED_MODEL = "all-MiniLM-L6-v2"

TOP_K = 5
USE_RERANK = os.getenv("USE_RERANK", "true").lower() == "true"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MIN_RELEVANCE = 0.15

LLM_MODE = os.getenv("LLM_MODE", "ollama")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
