import io
import os
import re
import json
import html
import datetime
import time
from pathlib import Path

import streamlit as st

import config
from answer import ask, format_citation
from index_store import count, build_index, load_store

try:
    from streamlit_mic_recorder import speech_to_text
    HAS_VOICE = True
except Exception:
    HAS_VOICE = False

st.set_page_config(page_title="VeriDoc", page_icon=":material/verified:", layout="wide")

ALLOWED_EXT = {".pdf", ".docx", ".txt"}
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

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


def confidence_badge(passages) -> tuple[str, str]:
    if not passages:
        return "No confidence", "gray"
    score = passages[0].score
    if score >= 0.65:
        label, color = "High confidence", "green"
    elif score >= 0.40:
        label, color = "Medium confidence", "orange"
    else:
        label, color = "Low confidence", "red"
    return f"{label} · {score:.0%}", color


def highlight_passage(text: str, query: str) -> str:
    safe = html.escape(text)
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
    with st.expander("Evidence used", icon=":material/library_books:"):
        for i, p in enumerate(passages):
            st.markdown(f"**{format_citation(p)}**")
            st.progress(max(0.0, min(1.0, p.score)), text=f"Relevance {p.score:.0%}")
            st.markdown(highlight_passage(p.text, query), unsafe_allow_html=True)
            source_path = config.DOCUMENTS_DIR / Path(p.source).name
            if source_path.is_file():
                st.download_button(
                    "Download original", source_path.read_bytes(), file_name=p.source,
                    mime="application/pdf" if source_path.suffix.lower() == ".pdf" else None,
                    icon=":material/download:", key=f"source_{i}_{p.source}",
                )


def deadline_alert(text: str):
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
    tops = passages[:2]
    if len(tops) < 2 or tops[0].source == tops[1].source:
        return False

    def dates(t):
        return set(re.findall(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", t))

    d0, d1 = dates(tops[0].text), dates(tops[1].text)
    return bool(d0 and d1 and not (d0 & d1))


def speak_button(text: str, lang: str = "en-US"):
    safe = json.dumps(text[:600]).replace("<", "\\u003c").replace(">", "\\u003e")
    lang_safe = re.sub(r"[^a-zA-Z-]", "", lang)
    st.components.v1.html(
        f"""<button id="veridoc-tts"
        style="background:#2E6DB4;color:#fff;border:none;padding:6px 14px;
        border-radius:8px;cursor:pointer;font-size:13px;">🔊 Listen</button>
        <script>
        document.getElementById("veridoc-tts").addEventListener("click", function() {{
            window.speechSynthesis.cancel();
            var u = new SpeechSynthesisUtterance({safe});
            u.lang = "{lang_safe}";
            window.speechSynthesis.speak(u);
        }});
        </script>""",
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
        txt = html.escape(turn["content"])
        if turn["role"] == "user":
            story.append(Paragraph("Q: " + txt, qs))
        else:
            story.append(Paragraph("A: " + txt, as_))
            srcs = "; ".join(format_citation(p) for p in (turn.get("passages") or []))
            if srcs:
                story.append(Paragraph("Sources: " + srcs, ss))
    doc.build(story)
    return buf.getvalue()


LANG_MAP = {
    "English": ("English", "en-US"),
    "हिंदी (Hindi)": ("Hindi (in Devanagari script)", "hi-IN"),
    "मराठी (Marathi)": ("Marathi (in Devanagari script)", "mr-IN"),
}


def clear_conversation():
    st.session_state.history = []
    st.session_state.num_q = 0
    st.session_state.likes = 0
    st.session_state.dislikes = 0

with st.sidebar:
    st.title(":material/verified: VeriDoc")
    st.caption("Grounded answers from approved documents")
    st.badge("System ready", icon=":material/check_circle:", color="green")

    # Dark mode toggle
    dark_mode = st.toggle("Dark mode", key="dark_mode")
    # Apply dark mode CSS
    if dark_mode:
        st.markdown("""
        <style>
        body { background-color: #111111; color: #eeeeee; }
        .stApp { background-color: #111111; color: #eeeeee; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body { background-color: #ffffff; color: #000000; }
        .stApp { background-color: #ffffff; color: #000000; }
        </style>
        """, unsafe_allow_html=True)

    lang_choice = st.segmented_control(
        "Language", list(LANG_MAP.keys()), default="English", key="answer_language"
    )
    language, tts_lang = LANG_MAP[lang_choice]
    simplify = st.toggle("Explain in simple language", key="simplify")
    detail = st.segmented_control(
        "Answer depth", ["Concise", "Detailed"], default="Concise",
        key="answer_depth",
    )

    st.subheader("Knowledge scope")
    store = load_store()
    docs = sorted(set(store["sources"]))
    if docs:
        selected_docs = st.multiselect(
            "Documents", docs, default=docs,
            help="Limit answers to selected official documents.",
        )
        st.caption(f"{len(store['ids'])} verified passages indexed")
        with st.expander("Browse library", icon=":material/folder_open:"):
            for i, name in enumerate(docs):
                path = config.DOCUMENTS_DIR / Path(name).name
                st.markdown(f":material/description: **{name}**")
                if path.is_file():
                    st.download_button(
                        "Download", path.read_bytes(), file_name=name,
                        mime="application/pdf" if path.suffix.lower() == ".pdf" else None,
                        icon=":material/download:", key=f"library_{i}", width="stretch",
                    )
    else:
        selected_docs = []
        st.warning("No documents are indexed.", icon=":material/warning:")

    with st.expander("Manage documents", icon=":material/upload_file:"):
        if not ADMIN_PASSWORD:
            st.caption("Admin upload is disabled. Set an ADMIN_PASSWORD secret to enable it.")
        else:
            pw = st.text_input("Admin password", type="password", key="admin_pw")
            if pw and pw != ADMIN_PASSWORD:
                st.error("Wrong password.")
            elif pw == ADMIN_PASSWORD:
                ups = st.file_uploader("Upload PDF / DOCX / TXT",
                                       type=["pdf", "docx", "txt"], accept_multiple_files=True)
                if st.button("Add and rebuild index", type="primary", width="stretch"):
                    if ups:
                        config.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
                        added = 0
                        for uf in ups:
                            safe_name = os.path.basename(uf.name)
                            ext = os.path.splitext(safe_name)[1].lower()
                            if ext not in ALLOWED_EXT or not safe_name:
                                st.warning(f"Skipped '{uf.name}' — type not allowed.")
                                continue
                            (config.DOCUMENTS_DIR / safe_name).write_bytes(uf.getbuffer())
                            added += 1
                        if added:
                            with st.spinner("Rebuilding index..."):
                                build_index()
                            st.success(f"Added {added} file(s) and rebuilt the index.")
                            st.rerun()
                    else:
                        st.warning("Choose at least one file first.")

    st.subheader("Current session")
    c1, c2, c3 = st.columns(3)
    c1.metric("Questions", st.session_state.num_q)
    c2.metric("👍", st.session_state.likes)
    c3.metric("👎", st.session_state.dislikes)

    if st.session_state.history:
        try:
            st.download_button("Download transcript",
                               data=build_chat_pdf(st.session_state.history),
                               file_name="veridoc_chat.pdf", mime="application/pdf",
                               icon=":material/download:", width="stretch")
        except Exception:
            txt = "\n\n".join(f"{t['role'].upper()}: {t['content']}" for t in st.session_state.history)
            st.download_button("Download transcript", data=txt,
                               file_name="veridoc_chat.txt",
                               icon=":material/download:", width="stretch")

        st.button("Clear conversation", on_click=clear_conversation,
                  icon=":material/delete_sweep:", width="stretch")

    st.caption(f"LLM: `{config.LLM_MODE}` · Re-ranking: {'on' if config.USE_RERANK else 'off'}")


header, status = st.columns([3, 1], vertical_alignment="center")
with header:
    st.title("Ask your official documents", anchor=False)
    st.caption("Answers are grounded in retrieved evidence and include source citations.")
with status:
    st.metric("Knowledge base", f"{len(docs)} documents", f"{len(store['ids'])} passages")


for i, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        if turn["role"] == "user":
            st.markdown(turn["content"])
            continue

        if turn.get("badge"):
            st.badge(turn["badge"], color=turn.get("badge_color", "gray"))
        st.markdown(turn["content"])
        if turn.get("elapsed") is not None:
            st.caption(f"Answered in {turn['elapsed']:.1f}s · {len(turn.get('passages') or [])} sources")

        if not turn.get("refused"):
            if turn.get("passages") and detect_conflict(turn["passages"]):
                st.warning("⚠️ Different documents mention different dates for this. "
                           "Showing the most relevant — please verify against the latest circular.")
            alert = deadline_alert(turn["content"])
            if alert:
                st.info(alert)

        if turn.get("passages"):
            render_sources(turn["passages"], turn.get("query", ""))

        if not turn.get("refused"):
            with st.container(horizontal=True):
                up = st.button("Helpful", icon=":material/thumb_up:", key=f"up_{i}")
                down = st.button("Needs work", icon=":material/thumb_down:", key=f"down_{i}")
            if up:
                st.session_state.likes += 1
            if down:
                st.session_state.dislikes += 1
            speak_button(turn["content"], turn.get("ttslang", "en-US"))


followup_q = None
if st.session_state.history and st.session_state.history[-1]["role"] == "assistant" \
        and not st.session_state.history[-1].get("refused"):
    asked = {t["content"] for t in st.session_state.history if t["role"] == "user"}
    suggestions = [q for q in FOLLOWUP_POOL if q not in asked][:3]
    if suggestions:
        followup_q = st.pills(
            "Continue exploring", suggestions,
            key=f"fu_{len(st.session_state.history)}", width="stretch"
        )


chip_q = None
if not st.session_state.history:
    feature_cols = st.columns(3)
    features = [
        (":material/fact_check:", "Evidence first", "Inspect the exact passages used for every answer."),
        (":material/gpp_good:", "Honest by design", "VeriDoc refuses when the documents do not support an answer."),
        (":material/translate:", "Multilingual", "Ask once and receive grounded answers in English, Hindi, or Marathi."),
    ]
    for col, (icon, title, text) in zip(feature_cols, features):
        with col.container(border=True, height="stretch"):
            st.subheader(f"{icon} {title}")
            st.caption(text)

    st.subheader("Start with a common question")
    examples = {
        ":material/payments: Fee deadline": "What is the last date to pay the fee?",
        ":material/school: Attendance": "What is the minimum attendance required?",
        ":material/workspace_premium: Scholarship": "Who is eligible for the merit scholarship?",
        ":material/calendar_month: Vacation": "When does the winter vacation begin?",
    }
    selected_example = st.pills(
        "Example questions", list(examples), label_visibility="collapsed",
        key="example_question", width="stretch",
    )
    chip_q = examples.get(selected_example)

voice_text = None
if HAS_VOICE:
    st.caption("🎤 Or ask by voice:")
    voice_text = speech_to_text(language="en", start_prompt="🎤 Speak",
                                stop_prompt="⏹ Stop", just_once=True, key="stt")

typed = st.chat_input("Ask about fees, exams, scholarships, policies, or dates…")
question = chip_q or followup_q or voice_text or typed

if question:
    if not selected_docs:
        st.warning("Select at least one document in the sidebar before asking.",
                   icon=":material/filter_alt:")
        st.stop()
    st.session_state.num_q += 1
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching official documents..."):
            started = time.perf_counter()
            try:
                result = ask(question, language=language, simplify=simplify,
                             detail=detail,
                             allowed_sources=set(selected_docs))
            except Exception as e:
                result = None
                st.error("Sorry, something went wrong while answering. Please try again.")
                print(f"[VeriDoc error] {e}")

        if result:
            elapsed = time.perf_counter() - started
            badge, badge_color = ("", "gray") if result.refused else confidence_badge(result.passages)
            if result.refused:
                st.warning(result.text)
            else:
                if badge:
                    st.badge(badge, color=badge_color)
                st.markdown(result.text)

            st.session_state.history.append({
                "role": "assistant",
                "content": result.text,
                "passages": result.passages,
                "refused": result.refused,
                "badge": badge,
                "badge_color": badge_color,
                "query": question,
                "ttslang": tts_lang,
                "elapsed": elapsed,
            })
            st.rerun()
