<!-- ====================== ANIMATED HEADER ====================== -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=1F335A&height=200&section=header&text=VeriDoc&fontSize=80&fontColor=ffffff&desc=Citation-Grounded%20Q%26A%20Assistant%20for%20Institutional%20Documents&descSize=18&descAlignY=72" width="100%"/>
</p>

<p align="center">
  <a href="https://veridoc-9td5zj9kteg5cly2vnaz6b.streamlit.app/">
    <img src="https://readme-typing-svg.demolab.com/?font=Segoe+UI&weight=600&size=24&pause=1000&color=2E6DB4&center=true&vCenter=true&width=650&lines=Answers+you+can+trust%2C+straight+from+the+source.;No+hallucinations+%E2%80%94+every+answer+is+cited.;Says+%22not+found%22+instead+of+guessing." alt="Typing SVG"/>
  </a>
</p>

<!-- ====================== BADGES ====================== -->
<p align="center">
  <a href="https://veridoc-9td5zj9kteg5cly2vnaz6b.streamlit.app/">
    <img src="https://img.shields.io/badge/%F0%9F%9A%80_Live_Demo-Open_App-2E6DB4?style=for-the-badge" alt="Live Demo"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/RAG-Retrieval_Augmented-1F335A?style=for-the-badge"/>
</p>

<p align="center">
  <b>🔗 Live app:</b>
  <a href="https://veridoc-9td5zj9kteg5cly2vnaz6b.streamlit.app/">veridoc-9td5zj9kteg5cly2vnaz6b.streamlit.app</a>
</p>

---

## 📌 What is VeriDoc?

**VeriDoc** answers questions about an institution — fees, exam rules, scholarships,
the academic calendar, hostel rules — using **only its official documents**.

Unlike a normal chatbot, VeriDoc:

- ✅ **Cites the source** for every answer (exact document + passage)
- 🚫 **Never hallucinates** — it refuses honestly when the answer isn't in the documents
- 🔍 **Understands meaning**, not just keywords (semantic search)

> The hard part everyone gets wrong — *grounding, citation, and honest refusal* — is
> exactly what VeriDoc is built around.

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🧠 | **Semantic search** | Finds the right passage even when the question is worded differently |
| 📎 | **Citations** | Every answer links back to the exact source text |
| 🛡️ | **Honest refusal** | Two-layer guard: a relevance gate + a strict grounding prompt |
| ⚡ | **Lightweight** | In-memory NumPy vector store — no heavy database, runs anywhere |
| 🔄 | **Swappable LLM** | Ollama (free, offline) locally · Google Gemini (free API) on the cloud |
| 🖥️ | **Simple UI** | Streamlit chat with an expandable "Show sources" panel |

---

## 🏗️ How it works

```
                ┌──────────── OFFLINE (once) ────────────┐
   Documents ─▶ Ingest + OCR ─▶ Chunk ─▶ Embed ─▶ Vector Store (NumPy)
                                                          │
                ┌──────────── ONLINE (per question) ──────┘
   Question ─▶ Retrieve + Re-rank ─▶ Relevance Gate ─▶ LLM (grounded) ─▶ Answer + Citation
                                          │
                                          └─▶ (low score) ─▶ "Not found in official documents"
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| UI | Streamlit |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector search | NumPy (in-memory cosine similarity) |
| Re-ranking | cross-encoder (`ms-marco-MiniLM`) — optional |
| LLM | Ollama · Llama 3 (local) / Google Gemini (cloud) |
| Doc parsing | PyMuPDF, python-docx, BeautifulSoup, Tesseract (OCR) |

---

## 🚀 Run it locally

```bash
# 1. clone
git clone https://github.com/govindturkar69-crypto/VeriDoc.git
cd VeriDoc

# 2. install
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt

# 3. (local LLM) install Ollama, then:
ollama pull llama3

# 4. add your PDFs to  documents/  then build the index
python index_store.py

# 5. launch
streamlit run app.py
```

Try asking: *"What is the last date to pay the fee?"* — then click **Show sources**.
Then ask something not in the documents to see the honest refusal.

---

## ☁️ Deployment

The live app runs on **Streamlit Community Cloud** using **Google Gemini** (free API tier),
since cloud hosting can't run a local model. See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the
full step-by-step guide. Local and cloud share the same code — only the LLM setting changes.

---

## 📊 Evaluation

VeriDoc is benchmarked on **61 real questions** (53 answerable + 8 unanswerable) and
compared against a keyword-search baseline and a plain chatbot.

```bash
python evaluation/compare.py
```

The key result: **only VeriDoc refuses correctly** on unanswerable questions, while the
baselines answer anyway — making VeriDoc the most trustworthy of the three.

---

## 📁 Project structure

```
veridoc/
├── documents/          # official institutional documents (PDF/DOCX/TXT)
├── ingest.py           # load + clean documents (with OCR)
├── index_store.py      # embed + build the NumPy vector index
├── retriever.py        # retrieve + re-rank passages
├── answer.py           # grounded answering (citation + honest refusal)
├── app.py              # Streamlit chat UI
├── evaluation/         # benchmark + three-way comparison
├── DEPLOYMENT.md       # cloud deployment guide
└── requirements.txt
```

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=1F335A&height=120&section=footer"/>
</p>

<p align="center"><i>Final Year Project · B.Tech Computer Science & Engineering</i></p>
