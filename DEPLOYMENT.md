# Deploying VeriDoc online (Streamlit Community Cloud)

This makes VeriDoc live at a public URL that anyone (including your examiner)
can open on a phone or laptop — no installation needed.

Because free cloud hosting cannot run Ollama, the cloud version uses
**Google Gemini** (free API tier). Your local version keeps using Ollama.
The code already supports both — you only change settings, not code.

---

## Step 1 — Get a free Gemini API key

1. Go to https://aistudio.google.com/app/apikey and sign in with a Google account.
2. Click **Create API key** and copy the key. Keep it private.

## Step 2 — Make sure your project is on GitHub

Your repo should already be pushed. If you changed files, push again:

```
git add .
git commit -m "Add cloud deployment (Gemini) support"
git push
```

Make sure the `documents/` folder (with your PDFs) is in the repo — the app
builds its search index from those files automatically on first run.

## Step 3 — Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io and sign in with your GitHub account.
2. Click **Create app -> Deploy a public app from GitHub**.
3. Fill in:
   - Repository: `govindturkar69-crypto/VeriDoc`
   - Branch: `main`
   - Main file path: `app.py`
4. Click **Advanced settings -> Secrets** and paste the following
   (replace with your real key):

   ```toml
   LLM_MODE = "gemini"
   GEMINI_API_KEY = "your_real_gemini_key_here"
   USE_RERANK = "false"
   ```

   `USE_RERANK = "false"` keeps memory low so it fits the free tier.

5. Click **Deploy**. The first build takes a few minutes (it installs
   packages and builds the document index). When it finishes you get a public
   URL like `https://veridoc-xxxx.streamlit.app`.

## Step 4 — Test the live app

Open the URL and ask a question (e.g. "What is the last date to pay the fee?").
Check that the answer appears with a citation, and that an unanswerable
question is politely refused.

---

## Notes & troubleshooting

- **Secrets = environment variables.** On Streamlit Cloud the secrets above are
  also exposed as environment variables, which `config.py` reads. You do not
  need a local `secrets.toml`.
- **Never commit your key.** `.gitignore` already excludes `.env` and
  `.streamlit/secrets.toml`. Only put the real key in the Cloud Secrets box.
- **Out of memory on build?** Make sure `USE_RERANK = "false"` is set. If it
  still struggles, also set embeddings to the small model (already the default,
  `all-MiniLM-L6-v2`).
- **App sleeps when idle.** Free apps go to sleep after inactivity and wake on
  the next visit (takes ~30 seconds). This is normal.
- **Local vs cloud.** Locally, do nothing — it keeps using Ollama. The cloud
  copy uses Gemini purely through the Secrets you set. Same code, both work.
