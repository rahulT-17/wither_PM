## WITHER — Weather Intelligence Terminal

# Overview
- WITHER is a lightweight weather intelligence dashboard that fetches weather and forecast data, summarizes results, and stores searchable historical queries. It’s built with a FastAPI backend and a React + TypeScript frontend.

# Key Features
- Natural-language weather queries ("weather in London this weekend").
- Geocoding, current conditions, and short-term forecast aggregation.
- Saved search history with deterministic deduplication (upsert by `search_key`).
- Export search snapshots as JSON/CSV/Markdown and request an AI-generated insight for a saved search.

# Quickstart — Development
Prereqs
- Python 3.11+ (or compatible), Node 18+, PostgreSQL running locally.
- Recommended: create a Python virtualenv for the backend.

Backend (FastAPI)
1. Create & activate the virtualenv from the `backend` folder:

```
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set values (do NOT commit `.env`):
```
cp .env.example .env
# edit .env and set DATABASE_URL, OPENWEATHER_API_KEY, ALLOWED_ORIGINS
```

3. Apply database migrations (Alembic). Important: Alembic expects a sync DB URL. If `DATABASE_URL` uses the async driver (asyncpg), set `DATABASE_URL_SYNC` in `.env` to a `postgresql+psycopg2://...` URL or edit `alembic/env.py` as directed.

```
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

4. Start the backend (development):

```
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Frontend (React + TypeScript)
1. From the `frontend` folder, install and build:

```
cd frontend
npm install
npm run build
```

2. Serve the `dist/` folder (the repo contains a simple static server script in `frontend/scripts/serve.mjs`), or run the local dev script that rebuilds and serves during development.

# Notes
- Backend API base URL expected by the frontend defaults to `http://127.0.0.1:8000/api/v1`. You can override at build time by setting `VITE_API_BASE_URL` when building the frontend.
- Keep secrets like `OPENWEATHER_API_KEY` out of source control. Rotate keys if they were committed previously.

# How to verify end-to-end
1. Run the backend and ensure it connects to Postgres and Alembic migrations applied.
2. Build and serve the frontend and open `http://localhost:5173`.
3. Type a natural-language weather query (e.g., "weather in Mumbai today").
4. Observe the summary, saved search in history, and try exporting or requesting an AI insight.

# Troubleshooting
- If Alembic errors with greenlet or async issues, ensure Alembic is using a sync driver (psycopg2) or set `DATABASE_URL_SYNC` in `.env`.
- If imports fail in the backend, confirm you activated the backend virtualenv and are running commands from the `backend` folder.

