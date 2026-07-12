# VeriDoc — Security Audit

Applied the 5 checks from *"5 Security Checks Before You Launch Your App"*
(Mayank Shah) to the VeriDoc codebase.

**Context:** VeriDoc is a Streamlit RAG app. It has **no login/auth, no payments,
no user database, no SQL, and collects no personal user data**. So several
checks don't apply — those are marked N/A honestly rather than pretending to
"fix" things that don't exist. The checks that *do* apply were fixed.

---

## 01 · Secret Leak Prevention (Gitleaks)

| Item | Status |
|---|---|
| API keys hardcoded in source? | ✅ None — all read from env vars (`os.getenv`) in `config.py` |
| `.env` in `.gitignore`? | ✅ Yes |
| `.env.example` with placeholders only? | ✅ Yes (no real secrets) |
| `.streamlit/secrets.toml` gitignored? | ✅ Yes |
| Secrets in logs / responses? | ✅ Errors no longer echo internals to the client |
| Frontend exposure (NEXT_PUBLIC_ etc.) | N/A — no React/Next front end |

**⚠️ Action required by you:** your Gemini API key was pasted in plain text while
debugging, so it is considered exposed. **Rotate it now:**
1. aistudio.google.com/app/apikey → delete the old key, create a new one.
2. Update `GEMINI_API_KEY` in Streamlit **Secrets** with the new key.

---

## 02 · Personal Data Flow Audit (Bearer)

Mostly **N/A** — VeriDoc collects no emails, passwords, names, or payment info.
- No signup, no accounts, no PII stored. ✅
- No passwords → nothing to hash. ✅
- No cookies/localStorage holding PII. ✅
- One data flow: the user's typed **question** is sent to the LLM (Gemini/Ollama).
  Users should avoid typing personal data into the question box. (Documented.)

---

## 03 · Pre-Deploy Production Audit (ECC)

| Check | Status |
|---|---|
| Env vars referenced safely, sensible defaults | ✅ |
| Debug endpoints (`/debug`, `/admin-backdoor`) | ✅ None — Streamlit has no such routes |
| Client error messages leak stack traces / paths? | ✅ **Fixed** — user sees a generic message; details go to server logs only |
| Security headers (HSTS, nosniff, CSP) | Handled by Streamlit Cloud (HTTPS enforced); custom headers not settable in Streamlit → N/A |
| Rate limiting on auth endpoints | N/A — no auth endpoints |
| CORS `*` | N/A — Streamlit manages this |
| Database TLS / open ports | N/A — no database (local NumPy vector store) |

---

## 04 · Deep Security Audit (Trail of Bits)

App has: **no payments, no custom auth, no smart contracts.** So auth/IDOR/JWT/
payment checks are N/A. The relevant part is **input handling**:

- **SQL injection:** ✅ N/A — no SQL anywhere (NumPy cosine-similarity store).
- **XSS (cross-site scripting):** ✅ **Fixed / verified**
  - Document text in the "sources" panel is now HTML-escaped before rendering.
  - The answer body is rendered with `st.markdown` (no raw HTML) — safe.
  - **Voice-answer button fixed:** the answer text is JSON-encoded and `<`/`>`
    are unicode-escaped, and the click handler uses `addEventListener` instead
    of an inline `onclick`. Previously an apostrophe or crafted text could break
    out of the attribute — now it cannot (this also fixed a real bug where any
    answer containing `'` broke the Listen button).
- **File uploads (admin):** ✅ **Fixed**
  - Filenames are sanitised with `os.path.basename` to block path traversal
    (e.g. `../../evil.py`).
  - Extensions are re-validated server-side against an allow-list (`.pdf/.docx/.txt`).

---

## 05 · Attacker's Perspective Review (ECC)

| Attack path | Status |
|---|---|
| Access other users' data via ID manipulation | N/A — no user IDs / accounts |
| Login bypass | N/A — no login |
| Privilege escalation (admin) | ✅ **Fixed** — the Admin "add documents" panel is now **password-gated** (`ADMIN_PASSWORD` secret). On the public app it stays locked, so visitors can't change the knowledge base |
| Content injection (XSS/SQLi) | ✅ Fixed / N/A (see check 04) |
| Internal exposure (env via errors, `.git`, `.env`) | ✅ Errors generic; `.env` & secrets gitignored |
| Business-logic abuse (payments) | N/A — no payments |

---

## Summary of changes made (in `app.py`)

1. **XSS-safe voice button** — encode text, escape `<`/`>`, use `addEventListener`.
2. **HTML-escape source text** before rendering in the sources panel.
3. **Admin upload password gate** via `ADMIN_PASSWORD` secret (locked by default).
4. **Path-traversal-safe uploads** — `os.path.basename` + server-side extension allow-list.
5. **Generic client errors** — no internal details leaked; full error to server log.

## Your to-do
- **Rotate the exposed Gemini API key** (most important).
- To use the admin panel on the live app, add an `ADMIN_PASSWORD` secret in
  Streamlit; otherwise it stays safely disabled.
- For an app handling real money/PII at scale you'd add a human security review —
  not needed here since VeriDoc stores no sensitive data.
