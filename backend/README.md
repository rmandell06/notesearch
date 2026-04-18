# Backend

FastAPI backend for the notes app.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Interactive docs at http://localhost:8000/docs.

## Test / Lint

```bash
pytest
pylint app/
```

## Layout

- `app/api/routes/` — HTTP endpoints grouped by resource.
- `app/core/` — config, exceptions, logging.
- `app/schemas/` — Pydantic request/response models.
- `app/services/` — one class per external system (storage, Supabase, Cloudflare Vectorize, embedding model, AWS Transcribe, connection graph).
- `app/models/` — internal DB row types.
- `tests/` — PyTest suite; `tests/experiments/` holds exploratory scripts excluded from coverage.
