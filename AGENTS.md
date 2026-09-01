# AI Agent Instructions for VeriDoc

## 1. Project Overview
You are working on **VeriDoc**, an institutional Retrieval-Augmented Generation (RAG) assistant. Its core purpose is to provide highly accurate, cited answers strictly from official documents, and to honestly refuse to answer when the information is missing.

**Priority Rule:** Never break the grounding mechanism. Hallucinations are the primary failure mode this project was built to solve.

## 2. Architecture Rules
- **Monolithic Web App:** The application is built entirely on Streamlit (`app.py`). There is no backend REST API or separate frontend framework.
- **Do not invent endpoints:** Do not try to add Express, FastAPI, or Flask routes. All UI/UX changes must be done using Streamlit components in `app.py`.
- **Vector Store Reality:** The directory is named `chroma_db/`, but **we do not use the ChromaDB library**. The vector store is a custom NumPy implementation serialized via `pickle`. Do not attempt to import or instantiate ChromaDB clients.

## 3. Important Directories and Files
- `app.py`: The Streamlit frontend. All UI changes go here.
- `ingest.py`: Document parsing and chunking. 
- `index_store.py`: Embedding generation and saving/loading the NumPy `store.pkl`.
- `retriever.py`: Cosine similarity search logic.
- `answer.py`: LLM orchestration and prompt generation.
- `documents/`: Directory where source files (PDFs, etc.) are placed before indexing.
- `evaluation/`: Benchmarking scripts and datasets.

## 4. Coding Conventions
- **Type Hinting:** Use Python 3.10+ type hints (`from __future__ import annotations`, `list[str]`, `str | None`).
- **Dataclasses:** Use `@dataclass` for structured data (e.g., `Chunk`, `Passage`, `Answer`).
- **Dependencies:** Limit new dependencies. The system is designed to run locally and lightweight.

## 5. Testing Rules
- Use Python's built-in `unittest` framework.
- When modifying retrieval or answering logic, mock out the heavy operations (embedding models and LLM API calls) using `unittest.mock.patch`, as seen in `test_retriever.py`.
- Run `evaluation/compare.py` if changing the core prompt or retrieval logic to ensure the hallucination prevention (honest refusal) metric doesn't degrade.

## 6. Sensitive Areas
- **`answer.SYSTEM_PROMPT`:** This prompt enforces the strict grounding and refusal behavior. Do not modify it unless explicitly instructed, as it directly impacts the evaluation benchmarks.
- **The Relevance Gate:** `retriever.py` uses `config.MIN_RELEVANCE`. Modifying this changes the strictness of the system.

## 7. Definition of Done
When implementing a change:
1. Ensure the Streamlit UI still functions without runtime errors.
2. Ensure no dependencies were added without explicit authorization.
3. If retrieval or logic changed, run `python -m unittest test_retriever.py` and ensure it passes.
