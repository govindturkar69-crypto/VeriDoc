# Testing Documentation

## 1. Testing Strategy
VeriDoc employs a hybrid testing approach:
1. **Unit Testing:** Using Python's standard `unittest` framework to verify backend logic (retrieval filtering, prompt construction).
2. **Benchmarking/Evaluation:** A custom evaluation script to test the core value proposition of the application: "honest refusal" and hallucination prevention against real-world documents.

## 2. Test Frameworks
- Unit Tests: `unittest` (standard library).
- Mocks: `unittest.mock.patch` for intercepting LLM calls and embedding model loads.
- Benchmarking: Custom Python script (`evaluation/compare.py`).

## 3. Unit Tests
- **Location:** `test_retriever.py` (root directory)
- **Coverage:**
  - `RetrieverTests.test_limits_results_to_selected_documents`: Verifies that the source filtering logic correctly isolates vector search results to only the allowed documents.
  - `AnswerTests.test_detailed_mode_changes_the_grounding_prompt`: Verifies that UI toggle settings (like "Detailed" mode) correctly alter the system prompt sent to the LLM.
- **Commands:** Run unit tests using standard `unittest`:
  ```bash
  python -m unittest test_retriever.py
  ```

## 4. Benchmarking and Evaluation
- **Location:** `evaluation/compare.py` and `evaluation/benchmark.csv`
- **Strategy:** Tests VeriDoc against a baseline keyword-search RAG and a vanilla (non-RAG) chatbot.
- **Dataset:** 61 real questions (53 answerable, 8 explicitly unanswerable).
- **Execution:**
  ```bash
  python evaluation/compare.py
  ```
- **Verification Goals:** 
  - The script asserts that VeriDoc correctly triggers the refusal state on the 8 unanswerable questions, proving that it does not hallucinate.
  - It outputs a CSV (`comparison.csv`) allowing developers to manually grade the answerable questions for accuracy.

## 5. Testing Gaps
- **UI/E2E Testing:** No automated UI tests (e.g., Selenium, Playwright, or Streamlit's native AppTest framework) exist to verify frontend behavior.
- **Ingestion Testing:** No automated unit tests for the document parsing logic (`ingest.py`), specifically the PDF extraction and OCR fallbacks.
