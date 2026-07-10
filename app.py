"""
Phase 5 — Streamlit chat UI.

Features: animated header, confidence badge, document panel, feedback buttons,
voice input, admin upload, Hindi/Hinglish answers, example chips, source
highlighting, follow-up suggestions, PDF export, deadline reminders,
conflicting-information detection, plain-language simplifier, voice answers.

Run with:
    streamlit run app.py
"""
import io
import re
import json
import datetime
from collections import defaultdict

import streamlit as st

import config
from answer import ask, format_citation
from index_store import count, build_index, load_store

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
    .veridoc-header {background:linear-gradient(120deg,#1F335A,#2E6DB4,#1F335A);
        background-size:200% 200%;animation:gradientShift 8s ease infinite;border-radius:16px;
        padding:26px 20px;text-align:center;color:#fff;margin-bottom:6px;box-shadow:0 6px 20px rgba(31,51,90,.25);}
    @keyframes gradientShift {0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    .veridoc-title {font-size:42px;font-weight:800;letter-spacing:1px;margin:0;animation:fadeInDown .9s ease both;}
    .veridoc-sub {font-size:15px;opacity:.92;margin-top:4px;animation:fadeInUp 1.1s ease both;}
    @keyframes fadeInDown {from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
    @keyframes fadeInUp {from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
    [data-testid="stChatMessage"] {animation:fadeInUp .5s ease both;}
    .live-dot {height:9px;width:9px;background:#3ddc84;border-radius:50%;display:inline-block;margin-right:6px;animation:pulse 1.5s infinite;}
    @keyframes pulse {0%{box-shadow:0 0 0 0 rgba(61,220,132,.6)}70%{box-shadow:0 0 0 8px rgba(61,220,132,0)}100%{box-shadow:0 0 0 0 rgba(61,220,132,0)}}
    .conf-badge {display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:700;color:#fff;margin-bottom:6px;}
    mark {background:#fff3b0;padding:0 2px;border-radius:3px;}
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

for k, v in {"likes": 0, "dislikes": 0, "num_q": 0, "history": []}.items():
    st.session_state.setdefault(k, v)

FOLLOWUP_POOL = [
    "What is the minimum attendance required?",
    "How much is the hostel fee per semester?",
    "Who is eligible for the merit scholarship?",
    "When does the winter vacation begin?",
    "What is the re-evaluation fee per subject?",
    "What are the library timings on weekdays?",
    "What is the anti-ragging helpline number?",
    "What is the late fee for paying after the due date?",
]
MONTHS = {m[:3]: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


# ---------------------------------------------------------------- helpers
def confidence_badge(passages) -> str:
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


def highlight_passage(text: str, query: str) -> str:
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    sentences = re.split(r"(?<=[.!?])\s+", safe)
    qwords = {w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2}
    best_i, best_score = -1, 0
    for i, s in enumerate(sentences):
        overlap = len(qwords & set(re.findall(r"[a-z0-9]+", s.lower())))
        if overlap > best_score:
            best_score, best_i = overlap, i
    if best_i >= 0 and best_score > 0:
        sentences[best_i] = f"<mark>{sentences[best_i]}</mark>"
    return " ".join(sentences)


def render_sources(passages, query=""):
    with st.expander("Show sources"):
        for p in passages:
            st.markdown(f"**{format_citation(p)}**  ·  relevance {p.score:.2f}")
            st.markdown(highlight_passage(p.text, query), unsafe_allow_html=True)
            st.divider()


def deadline_alert(text: str):
    """Find the soonest future date in the answer and report the countdown."""
    today = datetime.date.today()
    dates = []
    for m in re.finditer(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text):
        mo = MONTHS.get(m.group(2).lower()[:3])
        if not mo:
            continue
        try:
            dates.append(datetime.date(int(m.group(3)), mo, int(m.group(1))))
        except ValueError:
            continue
    future = [d for d in dates if (d - today).days >= 0]
    if not future:
        return None
    d = min(future)
    n = (d - today).days
    if n == 0:
        return f"⏰ This date is **today** ({d.strftime('%d %B %Y')})!"
    return f"⏰ Reminder: **{d.strftime('%d %B %Y')}** is in **{n} days**."


def detect_conflict(passages) -> bool:
    """Flag if two different documents give different key values (dates/amounts)."""
    by = defaultdict(set)
    for p in passages[:4]:
        vals = set(re.findall(r"Rs\.?\s*\d[\d,]+|\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d+%", p.text))
        if vals:
            by[p.source] |= vals
    groups = [v for v in by.values() if v]
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            if not (groups[a] & groups[b]):
                return True
    return False


def speak_button(text: str, lang: str = "en-US"):
    """Read the answer aloud using the browser's built-in speech synthesis.
    No Python package needed — works locally and on the cloud."""
    safe = json.dumps(text[:600])
    st.components.v1.html(
        f"""<button onclick='window.speechSynthesis.cancel();
        var u=new SpeechSynthesisUtterance({safe});u.lang="{lang}";
        window.speechSynthesis.speak(u);'
        style="background:#2E6DB4;color:#fff;border:none;padding:6px 14px;
        border-radius:8px;cursor:pointer;font-size:13px;">🔊 Listen</button>""",
        height=46,
    )


def build_chat_pdf(history) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    qs = ParagraphStyle("q", parent=styles["Normal"], fontName="Helvetica-Bold",
                        textColor=colors.HexColor("#2E6DB4"), fontSize=11, spaceBefore=10)
    as_ = ParagraphStyle("a", parent=styles["Normal"], fontSize=10, spaceAfter=4)
    ss = ParagraphStyle("s", parent=styles["Normal"], fontSize=8, textColor=colors.grey, spaceAfter=6)
    story = [Paragraph("VeriDoc — Conversation Transcript", styles["Title"]), Spacer(1, 8)]
    for turn in history:
        txt = turn["content"].replace("<", "&lt;").replace(">", "&gt;")
        if turn["role"] == "user":
            story.append(Paragraph("Q: " + txt, qs))
        else:
            story.append(Paragraph("A: " + txt, as_))
            srcs = "; ".join(format_citation(p) for p in (turn.get("passages") or []))
            if srcs:
                story.append(Paragraph("Sources: " + srcs, ss))
    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------- sidebar
LANG_MAP = {
    "English": ("English", "en-US"),
    "हिंदी (Hindi)": ("Hindi (in Devanagari script)", "hi-IN"),
    "Hinglish": ("Hinglish (Hindi written in English/Roman letters)", "en-US"),
}

with st.sidebar:
    st.header("⚙️ Settings")
    lang_choice = st.selectbox("Answer language", list(LANG_MAP.keys()))
    language, tts_lang = LANG_MAP[lang_choice]
    simplify = st.checkbox("🧒 Explain simply (plain language)")

    st.divider()
    st.header("📚 Loaded documents")
    store = load_store()
    docs = sorted(set(store["sources"]))
    if docs:
        for d in docs:
            st.write(f"• {d}")
        st.caption(f"{len(docs)} documents · {len(store['ids'])} passages indexed")
    else:
        st.write("No documents indexed yet.")

    with st.expander("🔧 Admin — add documents"):
        ups = st.file_uploader("Upload PDF / DOCX / TXT", type=["pdf", "docx", "txt"],
                               accept_multiple_files=True)
        if st.button("Add & rebuild index", use_container_width=True):
            if ups:
                config.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
                for uf in ups:
                    (config.DOCUMENTS_DIR / uf.name).write_bytes(uf.getbuffer())
                with st.spinner("Rebuilding index..."):
                    build_index()
                st.success(f"Added {len(ups)} file(s) and rebuilt the index.")
                st.rerun()
            else:
                st.warning("Choose at least one file first.")

    st.divider()
    st.header("📊 Session stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions", st.session_state.num_q)
    c2.metric("👍", st.session_state.likes)
    c3.metric("👎", st.session_state.dislikes)

    if st.session_state.history:
        try:
            st.download_button("⬇️ Download chat (PDF)",
                               data=build_chat_pdf(st.session_state.history),
                               file_name="veridoc_chat.pdf", mime="application/pdf",
                               use_container_width=True)
        except Exception:
            txt = "\n\n".join(f"{t['role'].upper()}: {t['content']}" for t in st.session_state.history)
            st.download_button("⬇️ Download chat (TXT)", data=txt,
                               file_name="veridoc_chat.txt", use_container_width=True)

    st.caption(f"LLM: `{config.LLM_MODE}` · Re-ranking: {'on' if config.USE_RERANK else 'off'}")


# ---------------------------------------------------------------- replay history
for i, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        if turn["role"] == "user":
            st.markdown(turn["content"])
            continue

        if turn.get("badge"):
            st.markdown(turn["badge"], unsafe_allow_html=True)
        st.markdown(turn["content"])

        if not turn.get("refused"):
            if turn.get("passages") and detect_conflict(turn["passages"]):
                st.warning("⚠️ Different documents mention different values for this. "
                           "Showing the most relevant — please verify against the latest circular.")
            alert = deadline_alert(turn["content"])
            if alert:
                st.info(alert)

        if turn.get("passages"):
            render_sources(turn["passages"], turn.get("query", ""))

        if not turn.get("refused"):
            b = st.columns([1, 1, 6])
            if b[0].button("👍", key=f"up_{i}"):
                st.session_state.likes += 1
            if b[1].button("👎", key=f"down_{i}"):
                st.session_state.dislikes += 1
            speak_button(turn["content"], turn.get("ttslang", "en-US"))


# ---------------------------------------------------------------- follow-up suggestions
followup_q = None
if st.session_state.history and st.session_state.history[-1]["role"] == "assistant" \
        and not st.session_state.history[-1].get("refused"):
    asked = {t["content"] for t in st.session_state.history if t["role"] == "user"}
    suggestions = [q for q in FOLLOWUP_POOL if q not in asked][:3]
    if suggestions:
        st.caption("💬 You might also ask:")
        cols = st.columns(len(suggestions))
        for j, sug in enumerate(suggestions):
            if cols[j].button(sug, key=f"fu_{len(st.session_state.history)}_{j}"):
                followup_q = sug


# ---------------------------------------------------------------- input area
chip_q = None
if not st.session_state.history:
    st.markdown("**💡 Try an example:**")
    examples = [
        "What is the last date to pay the fee?",
        "What is the minimum attendance required?",
        "Who is eligible for the merit scholarship?",
        "When does the winter vacation begin?",
    ]
    cols = st.columns(2)
    for idx, ex in enumerate(examples):
        if cols[idx % 2].button(ex, key=f"ex_{idx}", use_container_width=True):
            chip_q = ex

voice_text = None
if HAS_VOICE:
    st.caption("🎤 Or ask by voice:")
    voice_text = speech_to_text(language="en", start_prompt="🎤 Speak",
                                stop_prompt="⏹ Stop", just_once=True, key="stt")

typed = st.chat_input("Ask about fees, exams, scholarships, calendar...")
question = chip_q or followup_q or voice_text or typed

if question:
    st.session_state.num_q += 1
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching official documents..."):
            try:
                result = ask(question, language=language, simplify=simplify)
            except Exception as e:
                result = None
                st.error(f"Error: {e}\n\nDid you run `python index_store.py` first?")

        if result:
            badge = "" if result.refused else confidence_badge(result.passages)
            if result.refused:
                st.warning(result.text)
            else:
                if badge:
                    st.markdown(badge, unsafe_allow_html=True)
                st.markdown(result.text)

            st.session_state.history.append({
                "role": "assistant",
                "content": result.text,
                "passages": result.passages,
                "refused": result.refused,
                "badge": badge,
                "query": question,
                "ttslang": tts_lang,
            })
            st.rerun()
