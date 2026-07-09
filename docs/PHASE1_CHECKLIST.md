# Phase 1 — Research & Planning Checklist (Weeks 1–2)

Start here. This phase needs no coding and unblocks everything else.

## A. Collect real documents (highest priority — depends on other people)
- [ ] Fee circular / fee structure (current year)
- [ ] Examination rules & regulations
- [ ] Scholarship / financial-aid policy
- [ ] Academic calendar
- [ ] Hostel rules
- [ ] Admission brochure / prospectus
- [ ] Any FAQ pages from the college website (save as .html or .pdf)

Put every file into the `documents/` folder. Note the source and date of
each — you'll cite these.

## B. Understand the real problem
- [ ] Ask 8–10 students which info is hardest to find, and how they find it now
- [ ] Note 3–4 real complaints (wrong answer from staff, missed deadline, etc.)
- [ ] Write a one-paragraph problem statement in your own words

## C. Build the seed benchmark (you'll grow it to ~120 in Phase 6)
- [ ] Collect 30+ real questions students actually ask
- [ ] For each, note the correct answer AND which document it's in
- [ ] Add 8–10 "unanswerable" questions (info NOT in any document) to test refusal
- [ ] Enter them into `evaluation/benchmark.csv`

## D. Environment ready
- [ ] Python + virtual environment installed
- [ ] `pip install -r requirements.txt` runs cleanly
- [ ] GitHub repo created and first commit pushed
- [ ] Decide LLM mode (Ollama offline vs OpenAI API) and set it in `config.py`
- [ ] Run the sample: `python index_store.py` then `streamlit run app.py`

## E. Get sign-off
- [ ] Share the proposal + this plan with your guide and get approval to build

When A–E are done, move to Phase 2 (ingestion) — the code is already there.
