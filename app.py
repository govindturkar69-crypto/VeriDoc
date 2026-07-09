"""
Phase 5 — Streamlit chat UI.

Run with:
    streamlit run app.py

Shows the answer plus an expandable "Sources" panel so every answer
can be verified against the original document text.
"""
import streamlit as st

import config
from answer import ask, format_citation
from index_store import count, build_index

st.set_page_config(page_title="VeriDoc", page_icon="📄", layout="centered")


@st.cache_resource(show_spinner="Building the document index (first run only)...")
def _ensure_index():
    """Build the search index automatically if it doesn't exist yet.
    This lets the app run on cloud hosting without a manual index step."""
    if count() == 0:
        build_index()
    return True


_ensure_index()

st.title("📄 VeriDoc")
st.caption("Answers you can trust, straight from the source.")

with st.sidebar:
    st.header("About")
    st.write(
        "VeriDoc answers questions **only** from your college's official "
        "documents. If the answer isn't there, it says so instead of guessing."
    )
    st.divider()
    st.write(f"**LLM mode:** `{config.LLM_MODE}`")
    st.write(f"**Top-K passages:** {config.TOP_K}")
    st.write(f"**Re-ranking:** {'on' if config.USE_RERANK else 'off'}")
    st.caption("Change settings in config.py, then rebuild with "
               "`python index_store.py`.")

if "history" not in st.session_state:
    st.session_state.history = []

# Replay conversation
for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("passages"):
            with st.expander("Show sources"):
                for p in turn["passages"]:
                    st.markdown(f"**{format_citation(p)}**  ·  relevance {p.score:.2f}")
                    st.write(p.text)
                    st.divider()

question = st.chat_input("Ask about fees, exams, scholarships, calendar...")
if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching official documents..."):
            try:
                result = ask(question)
            except Exception as e:
                result = None
                st.error(f"Error: {e}\n\nDid you run `python index_store.py` first?")

        if result:
            if result.refused:
                st.warning(result.text)
            else:
                st.markdown(result.text)
                if result.passages:
                    with st.expander("Show sources"):
                        for p in result.passages:
                            st.markdown(f"**{format_citation(p)}**  ·  relevance {p.score:.2f}")
                            st.write(p.text)
                            st.divider()

            st.session_state.history.append({
                "role": "assistant",
                "content": result.text,
                "passages": result.passages,
            })
