"""
Phase 5 — Streamlit chat UI (animations + confidence badge, document panel,
feedback buttons, and voice input).

Run with:
    streamlit run app.py
"""
import streamlit as st

import config
from answer import ask, format_citation
from index_store import count, build_index, load_store

# Optional voice input (browser speech-to-text). If the package isn't
# installed the app still works — the mic button just won't appear.
try:
    from streamlit_mic_recorder import speech_to_text
    HAS_VOICE = True
except Exception:
    HAS_VOICE = False

st.set_page_config(page_title="VeriDoc", page_icon="📄", layout="centered")

# ---------------------------------------------------------------- styling / animation
st.markdown(
    """
    <style>
    .veridoc-header {
        background: linear-gradient(120deg, #1F335A, #2E6DB4, #1F335A);
        background-size: 200% 200%; animation: gradientShift 8s ease infinite;
        border-radius: 16px; padding: 26px 20px; text-align: center;
        color: #fff; margin-bottom: 6px; box-shadow: 0 6px 20px rgba(31,51,90,0.25);
    }
    @keyframes gradientShift {0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    .veridoc-title {font-size:42px;font-weight:800;letter-spacing:1px;margin:0;animation:fadeInDown .9s ease both;}
    .veridoc-sub {font-size:15px;opacity:.92;margin-top:4px;animation:fadeInUp 1.1s ease both;}
    @keyframes fadeInDown {from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
    @keyframes fadeInUp {from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
    [data-testid="stChatMessage"] {animation: fadeInUp .5s ease both;}
    .live-dot {height:9px;width:9px;background:#3ddc84;border-radius:50%;display:inline-block;margin-right:6px;animation:pulse 1.5s infinite;}
    @keyframes pulse {0%{box-shadow:0 0 0 0 rgba(61,220,132,.6)}70%{box-shadow:0 0 0 8px rgba(61,220,132,0)}100%{box-shadow:0 0 0 0 rgba(61,220,132,0)}}
    .conf-badge {display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:700;color:#fff;margin-bottom:6px;}
    </style>
    <div class="veridoc-header">
        <p class="veridoc-title">📄 VeriDoc</p>
        <p class="veridoc-sub">Answers you can trust, straight from the source.</p>
    </div>
    <p style="text-align:center;color:#3ddc84;font-size:13px;margin-top:2px;">
        <span class="live-dot"></span> grounded &amp; citation-backed
    </p>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Building the document index (first run only)...")
def _ensure_index():
    if count() == 0:
        build_index()
    return True


_ensure_index()


# ---------------------------------------------------------------- helpers
def confidence_badge(passages) -> str:
    """Return an HTML badge based on the top passage's relevance score."""
    if not passages:
        return ""
    score = passages[0].score
    if score >= 0.65:
        label, color = "High confidence", "#1D9E75"
    elif score >= 0.40:
        label, color = "Medium confidence", "#D8912E"
    else:
        label, color = "Low confidence", "#D85A30"
    return f'<span class="conf-badge" style="background:{color};">{label} · {score:.0%}</span>'


def render_sources(passages):
    with st.expander("Show sources"):
        for p in passages:
            st.markdown(f"**{format_citation(p)}**  ·  relevance {p.score:.2f}")
            st.write(p.text)
            st.divider()


# ---------------------------------------------------------------- sidebar: docs + stats
for k, v in {"likes": 0, "dislikes": 0, "num_q": 0, "history": []}.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.header("📚 Loaded documents")
    store = load_store()
    docs = sorted(set(store["sources"]))
    if docs:
        for d in docs:
            st.write(f"• {d}")
        st.caption(f"{len(docs)} documents · {len(store['ids'])} passages indexed")
    else:
        st.write("No documents indexed yet.")

    st.divider()
    st.header("📊 Session stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions", st.session_state.num_q)
    c2.metric("👍", st.session_state.likes)
    c3.metric("👎", st.session_state.dislikes)

    st.divider()
    st.caption(f"LLM mode: `{config.LLM_MODE}` · Re-ranking: "
               f"{'on' if config.USE_RERANK else 'off'}")


# ---------------------------------------------------------------- replay history
for i, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        if turn["role"] == "assistant" and turn.get("badge"):
            st.markdown(turn["badge"], unsafe_allow_html=True)
        st.markdown(turn["content"])
        if turn.get("passages"):
            render_sources(turn["passages"])
        if turn["role"] == "assistant" and not turn.get("refused"):
            fb = st.columns([1, 1, 8])
            if fb[0].button("👍", key=f"up_{i}"):
                st.session_state.likes += 1
            if fb[1].button("👎", key=f"down_{i}"):
                st.session_state.dislikes += 1


# ---------------------------------------------------------------- input (text + voice)
voice_text = None
if HAS_VOICE:
    st.caption("🎤 Or ask by voice:")
    voice_text = speech_to_text(language="en", start_prompt="🎤 Speak",
                                stop_prompt="⏹ Stop", just_once=True, key="stt")

typed = st.chat_input("Ask about fees, exams, scholarships, calendar...")
question = voice_text or typed

if question:
    st.session_state.num_q += 1
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
            badge = ""
            if result.refused:
                st.warning(result.text)
            else:
                badge = confidence_badge(result.passages)
                if badge:
                    st.markdown(badge, unsafe_allow_html=True)
                st.markdown(result.text)
                if result.passages:
                    render_sources(result.passages)

            st.session_state.history.append({
                "role": "assistant",
                "content": result.text,
                "passages": result.passages,
                "refused": result.refused,
                "badge": badge,
            })
            st.rerun()
