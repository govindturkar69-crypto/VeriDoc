# API Documentation

## 1. Overview
The VeriDoc application is a standalone Streamlit web application. **It does not expose any public HTTP/REST APIs or WebSocket endpoints** for external clients to consume. 

All interactions occur via the Streamlit frontend UI.

## 2. Internal Subsystem APIs (Python API)
While no HTTP APIs exist, the backend functionality is modularized. If developers need to programmatically interact with VeriDoc, they must import the Python functions directly.

### Retrieval API
`retriever.retrieve(question: str, top_k: int | None = None, allowed_sources: set[str] | None = None) -> list[Passage]`
- **Purpose:** Performs semantic search against the loaded document index.
- **Parameters:**
  - `question`: The search query.
  - `top_k`: Number of results to return (defaults to `config.TOP_K`).
  - `allowed_sources`: A set of filenames to restrict the search to.
- **Returns:** A list of `Passage` dataclass instances containing text, source, page, and similarity score.

### Answer Generation API
`answer.ask(question: str, language: str = "English", simplify: bool = False, detail: str = "Concise", allowed_sources: set[str] | None = None) -> Answer`
- **Purpose:** Retrieves passages and prompts the LLM to answer the question based strictly on those passages.
- **Parameters:**
  - `question`: The user's query.
  - `language`: Target language for the answer.
  - `simplify`: If True, instructs the LLM to use simple language.
  - `detail`: "Concise" or "Detailed" instruction for the LLM.
  - `allowed_sources`: A set of filenames to restrict the search to.
- **Returns:** An `Answer` dataclass instance containing the LLM response text, the passages used, and a boolean indicating if the system refused to answer.

## 3. External APIs Consumed
The application acts as a client to external LLM APIs depending on the configuration:
- **Google Gemini API:** Accessed via `google-generativeai` package.
- **OpenAI API:** Accessed via `openai` package.
- **Ollama API:** Accessed via local HTTP requests (`http://localhost:11434/api/generate`) using `urllib.request`.
