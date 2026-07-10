"""
Phase 5 — Streamlit chat UI (with CSS animations).

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


# ---------------------------------------------------------------- animations / styling
st.markdown(
    """
    <style>
    /* ---- animated gradient header banner ---- */
    .veridoc-header {
        background: linear-gradient(120deg, #1F335A, #2E6DB4, #1F335A);
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        border-radius: 16px;
        padding: 26px 20px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 6px;
        box-shadow: 0 6px 20px rgba(31,51,90,0.25);
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .veridoc-title {
        font-size: 42px; font-weight: 800; letter-spacing: 1px; margin: 0;
        animation: fadeInDown 0.9s ease both;
    }
    .veridoc-sub {
        font-size: 15px; opacity: 0.92; margin-top: 4px;
        animation: fadeInUp 1.1s ease both;
    }
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    /* ---- fade-in for chat messages ---- */
    [data-testid="stChatMessage"] {
        animation: fadeInUp 0.5s ease both;
    }
    /* ---- pulsing live dot ---- */
    .live-dot {
        height: 9px; width: 9px; background:#3ddc84; border-radius:50%;
        display:inline-block; margin-right:6px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(61,220,132,0.6); }
        70%  { box-shadow: 0 0 0 8px rgba(61,220,132,0); }
        100% { box-shadow: 0 0 0 0 rgba(61,220,132,0); }
    }
    /* ---- chat input accent ---- */
    [data-testid="stChatInput"] textarea:focus {
        border-color: #2E6DB4 !important;
    }
    </style>

    <div class="veridoc-header">
        <p class="veridoc-title">📄 VeriDoc</p>
        <p class="veridoc-sub">Answers you can trust, straight from the source.</p>
    </div>
    <p style="text-align:center; color:#3ddc84; font-size:13px; margin-top:2px;">
        <span class="live-dot"></span> grounded &amp; citation-backed
    </p>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Building the document index (first run only)...")
def _ensure_index():
    """Build the search index automatically if it doesn't exist yet.
    This lets the app run on cloud hosting without a manual index step."""
    if count() == 0:
        build_index()
    return True


_ensure_index()

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
