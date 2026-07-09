# VeriDoc — Citation-Grounded Q&A Assistant for Institutional Documents

> "Answers you can trust, straight from the source."

VeriDoc answers questions about your college **only** from official documents.
Every answer shows the exact source, and it says *"not found in the official
documents"* instead of guessing. This is the whole point — no hallucinations.

---

## 1. What this starter gives you

A working Retrieval-Augmented Generation (RAG) skeleton:

```
veridoc/
├── documents/          <- put your college PDFs / DOCX / TXT here
├── config.py           <- all settings in one place
├── ingest.py           <- Phase 2: load + clean documents (with OCR)
├── index_store.py      <- Phase 3: chunk + embed + store in ChromaDB
├── retriever.py        <- Phase 3: retrieve + re-rank passages
├── answer.py           <- Phase 4: grounded answer with citation / refusal
├── app.py              <- Phase 5: Streamlit chat UI
├── evaluation/         <- Phase 6: benchmark template
├── requirements.txt
└── .env.example        <- copy to .env and add your API key (if using one)
```

## 2. Setup (do this first)

```bash
# 1. create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. (only if you use an API model) copy env file and add your key
cp .env.example .env        # then edit .env
```

You also need **Tesseract** installed for OCR of scanned PDFs:
- Windows: download the installer from the Tesseract-OCR project.
- Mac: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

## 3. Choose your LLM (two options)

Open `config.py` and set `LLM_MODE`:

- `"ollama"` — free & offline. Install Ollama, then `ollama pull llama3`.
- `"openai"` — easier/higher quality. Put your key in `.env`.

The retrieval + embeddings run locally and are free in both cases.

## 4. Run it

```bash
# Step A: put a few college PDFs into  documents/
# Step B: build the search index
python index_store.py

# Step C: launch the app
streamlit run app.py
```

Ask a question, read the answer, and click "Show sources" to verify it.

## 5. Where each project phase lives

| Phase | File(s) | Status in starter |
|---|---|---|
| 1. Research & planning | `docs/PHASE1_CHECKLIST.md` | checklist provided |
| 2. Document ingestion | `ingest.py` | working |
| 3. Retrieval | `index_store.py`, `retriever.py` | working |
| 4. Grounded answering | `answer.py` | working (core logic) |
| 5. User interface | `app.py` | working |
| 6. Evaluation | `evaluation/benchmark.csv`, `evaluation/evaluate.py` | template |

## 6. Your job from here (this is the real project work)

- Phase 1: fill `documents/` with **real** college files and build the benchmark.
- Phase 4: tune the prompt in `answer.py` so refusals are reliable.
- Phase 6: expand `evaluation/benchmark.csv` to ~120 questions and compare
  against keyword search + a vanilla chatbot. This comparison is your
  main contribution — don't skip it.

Good luck. Commit to GitHub early and often.
