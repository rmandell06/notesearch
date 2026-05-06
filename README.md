# Notesearch

Semantic note search over your own notes. A custom transformer encoder (RoPE + SiLU + SwiGLU) trained on NLI entailment pairs produces 128-dim embeddings; Cloudflare Vectorize stores and ranks them; Supabase handles auth and the notes table; FastAPI serves the API; React renders the UI.

## Try the live demo

**→ [notesearch-three.vercel.app](https://notesearch-three.vercel.app)**

Sign up with any email + 8-character password, drop in a `.txt`, `.md`, or `.pdf`, and search semantically. Frontend on Vercel, backend on Render free tier (`notesearch-9vjs.onrender.com`).

A few caveats so you're not surprised:

- **First request after idle is slow.** Render's free tier sleeps the container after 15 minutes of no traffic. The cold start takes ~30 seconds the first time you hit the site, then everything is fast for the rest of your session.
- **Cloudflare Vectorize indexing has ~5 second latency.** Right after you upload a note, the search may not return it for a few seconds. Refresh and retry.
- **Email confirmation is disabled** on the demo Supabase project, so any plausible email works for sign-up.
- **Don't upload anything sensitive** — the demo runs on shared keys and the data sits in a project that may be wiped after grading.

If you want to run it on your own infrastructure with your own data, follow the setup below.

## What's in this repo

```
backend/         FastAPI app + ML pipeline
  app/api/       HTTP routes (auth, notes, search, connections, voice)
  app/services/  encoder, tokenizer, embedding, vector_store, supabase_client
  app/artifacts/ trained encoder.pt + config.json + tokenizer JSON
  migrations/    SQL for the Supabase notes table
  tests/         pytest suite (50+ tests, mocks Supabase + Cloudflare)

frontend/        React app (Create React App)
  src/pages/     Home, SearchResults, NoteViewer, Connections, Login, Signup
  src/components/ TopNav, SearchBar, NoteCard, UploadArea, StatsPanel
```

## Prerequisites

- **Python 3.11** (the trained encoder ships with the repo and was saved against this version)
- **Node 18+** and **npm**
- A **Supabase** project — free tier is fine
- A **Cloudflare** account with **Workers** + **Vectorize** enabled
- ~13 MB free disk space (for the bundled encoder weights)

## 1. Clone and pick the right branch

```bash
git clone https://github.com/SP26-UIUC-CS222/Team-26.058.git
cd Team-26.058
git checkout bobbym3   # or whatever branch you're working on
```

## 2. Set up Supabase

1. Create a new project at https://supabase.com/dashboard
2. **Project Settings → API**, copy:
   - `Project URL` (e.g. `https://abcdefg.supabase.co`)
   - `service_role` key (the long JWT — *not* the anon/publishable key)
3. **Authentication → Providers → Email** — uncheck **"Confirm email"** for the demo (so signups return an access token immediately).
4. **SQL Editor → New query** — paste the contents of [`backend/migrations/0001_notes_schema.sql`](backend/migrations/0001_notes_schema.sql) and run it. Confirm the destructive-operation warning if it appears (it's just `DROP POLICY IF EXISTS`, idempotent).

## 3. Set up Cloudflare Vectorize

You need an index at **dimension 128, metric cosine** to match the encoder output.

**Via Wrangler CLI:**
```bash
npm install -g wrangler
wrangler login
wrangler vectorize create notes-index --dimensions=128 --metric=cosine
```

**Or via dashboard:** Cloudflare → AI → Vectorize → Create index. Name it `notes-index` (or anything — just match the env var below), dimensions `128`, metric `cosine`.

Then create an API token at **My Profile → API Tokens → Create Custom Token** with:
- `Account → Vectorize → Edit`
- `Account → Vectorize → Read`
- Account resource set to your specific account, not "All accounts"

Copy the token — you only see it once.

Your account ID is in the dashboard at top right (32 hex chars).

## 4. Backend setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate                        # Windows: .venv\Scripts\activate
pip install -r requirements.txt                  # ~3-5 minutes; pulls torch
```

Create `backend/.env` (this file is gitignored):

```bash
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./storage

SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=eyJ...your-service-role-key...

CLOUDFLARE_ACCOUNT_ID=your-32-hex-account-id
CLOUDFLARE_API_TOKEN=your-vectorize-token
CLOUDFLARE_VECTORIZE_INDEX=notes-index
```

Verify everything wires up:

```bash
pytest tests/                                    # all 50 tests should pass
uvicorn app.main:app --reload --port 8000
```

Sanity check:
```bash
curl http://localhost:8000/health                # → {"status":"ok"}
```

Interactive API docs: http://localhost:8000/docs

## 5. Frontend setup

In a separate terminal:

```bash
cd frontend
npm install                                      # ~2-3 minutes
npm start                                        # opens http://localhost:3000
```

If port 3000 is taken, use `PORT=5173 npm start`.

The frontend defaults to `http://localhost:8000` for the API. To override, create `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
```

## 6. End-to-end smoke test

With both servers running and Supabase / Cloudflare configured:

1. Open http://localhost:3000 → sign up with any email + 8-char password
2. Click **+ Upload note**, drop a `.txt`, `.md`, or `.pdf` file
3. Wait ~5 seconds for Cloudflare to index the new vectors
4. Type a semantic query in the search bar (e.g. "team progress" if you uploaded a meeting note)
5. Click a result → see the note body and "Related notes" sidebar with similarity scores
6. **Connections** in the top nav → force-directed graph of all your notes

## Architecture quick reference

```
upload  →  pdfplumber/utf-8 text extraction
       →  word-bounded chunking (≈200 words, 32 overlap)
       →  BPE tokenization (custom 10k-token vocab)
       →  Encoder.forward (6-layer transformer, RoPE attention, SiLU FFN)
       →  mean pool to 128-dim
       →  Vectorize upsert with metadata (note_id, chunk_index, snippet, …)

search →  same embedding pipeline on the query
       →  Vectorize query (cosine, top_k * 5)
       →  dedupe by note_id, keep best chunk per note
       →  return top_k with title + preview + relevance
```

## Common issues

| Symptom | Fix |
|---|---|
| Backend `503 SUPABASE_URL ... must be set` | `.env` missing or has empty values |
| Backend `503 CLOUDFLARE_*` | Same, for the three CF vars |
| `400 Email address invalid` on signup | Supabase email validation — use a real-looking domain (`@gmail.com` works for testing) |
| Signup returns 200 but `access_token: null` | Email confirmation is on — disable it in Supabase Auth → Providers → Email |
| `RuntimeError: Error(s) in loading state_dict for Encoder` | `encoder.py` architecture and `encoder.pt` weights mismatched — pull the canonical pair from `backend/artifacts/` |
| Search returns `[]` after upload | Cloudflare indexing latency (~5s on free tier). Wait and retry. |
| PDF preview shows binary garbage | Re-upload — the pdfplumber path landed in commit `f342691`. Old uploads from before that need to be re-created. |
| Frontend `Failed to fetch` | Backend isn't running, wrong port, or CORS — check `app.main:app` is on port 8000 |

## Tests

```bash
cd backend && pytest tests/ -v
```

50+ tests, ≥80% coverage. Mocks Supabase and Cloudflare so the suite runs without credentials.

## Out of scope (intentionally stubbed)

- `POST /voice/` — AWS Transcribe upload + polling (returns 501)
- `/connections/` graph quality is currently a Jaccard token-overlap fallback; cosine over real embeddings is what the encoder enables but isn't wired into the connections route yet

## Authors

CS222 SP26 — Team 26.058: Robert Mandell, Pranav Popuri, Surya Sridharan, Aashna Anand
Frontend - Aashna
Backend - Surya and Robert
Transformer - Robert and Pranav
