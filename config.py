"""
VeriDoc — central configuration.
Change settings here; the rest of the code reads from this file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
USE_RERANK = True       # set False if you want faster (less accurate) results
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# The retrieval score below which we treat the question as "not answerable".
# Tune this in Phase 4 using your benchmark — it controls honest refusal.
MIN_RELEVANCE = 0.15

# --- LLM ---
# "ollama"  -> free, offline (install Ollama + `ollama pull llama3`)
# "openai"  -> needs OPENAI_API_KEY in .env
LLM_MODE = "ollama"
OLLAMA_MODEL = "llama3"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
