# Technical Requirements Document (TRD)

## 1. Technical Overview
VeriDoc is a Retrieval-Augmented Generation (RAG) application built primarily with Python. It uses Streamlit for the user interface, custom in-memory vector storage for retrieval, and integrates with large language models (LLMs) via APIs or local inference to generate grounded responses.

## 2. Technology Stack

### Core Languages and Frameworks
- **Programming Language:** Python (3.10+)
- **Frontend/UI Framework:** Streamlit (`streamlit`)

### Core Libraries (Versions as per `requirements.txt`)
- **Embeddings:** `sentence-transformers`
- **Vector Operations:** `numpy`
- **Document Loading & Processing:**
  - PDFs: `pymupdf` (fitz)
  - Word Docs: `python-docx`
  - HTML: `beautifulsoup4`
  - Images/OCR: `pytesseract`, `Pillow`
- **UI Extensions:** `streamlit-mic-recorder`, `reportlab`
- **Configuration:** `python-dotenv`

### Models and AI
- **Embedding Model:** `all-MiniLM-L6-v2` (via `sentence-transformers`)
- **Reranker Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (optional, enabled by default)
- **Supported LLMs:**
  - Local: Ollama (`llama3` default)
  - Cloud: Google Gemini (`gemini-2.5-flash` default), OpenAI (`gpt-4o-mini` default)

## 3. Runtime Environment
- **Local:** Runs locally on any OS supporting Python and Streamlit.
- **Cloud:** Designed to be easily deployable on Streamlit Community Cloud (using cloud LLMs like Gemini or OpenAI since local models cannot run there).

## 4. Components Implementation Details
- **Frontend:** Handled entirely by `app.py` utilizing Streamlit's chat interface components.
- **Backend (Retrieval):** Handled by `retriever.py` and `index_store.py`. Vector similarity is computed using dot product on normalized numpy arrays.
- **Database:** No external database engine. A custom implementation storing document metadata and numpy embedding vectors in a serialized Python Pickle file (`store.pkl`).

## 5. Configuration & Environment Variables
Configured via `.env` file or environment variables, loaded by `config.py`:
- `LLM_MODE`: `ollama`, `gemini`, or `openai`.
- `GEMINI_API_KEY`: API key for Google Gemini.
- `OPENAI_API_KEY`: API key for OpenAI.
- `GEMINI_MODEL`: Specific Gemini model to use (default: `gemini-2.5-flash`).
- `OPENAI_MODEL`: Specific OpenAI model to use (default: `gpt-4o-mini`).
- `USE_RERANK`: Boolean to enable/disable cross-encoder re-ranking.

## 6. Error Handling
- **LLM Failures:** Caught in `answer.py`, returning a safe `[LLM error: <error>]` message without crashing the application.
- **Gemini Model Fallbacks:** Iterates through a list of supported Gemini models (`gemini-2.5-flash`, `gemini-2.0-flash`, etc.) and falls back to listing available models if the default fails.
- **OCR Failures:** If Tesseract OCR fails on an image/page, the error is caught, printed, and skipped, allowing ingestion to continue.

## 7. Performance and Constraints
- **In-Memory Store:** The entire index (embeddings and text) is loaded into RAM. Performance and capacity are constrained by the host machine's memory.
- **Embedding Compute:** Embedding generation runs locally on the CPU (by default for `sentence-transformers`), which can be slow for large document batches without GPU acceleration.
- **Reranking:** Cross-encoder reranking adds latency to retrieval but improves accuracy.
