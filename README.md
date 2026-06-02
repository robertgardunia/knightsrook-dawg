# knightsrook-dawg

Reconstructive memory substrate — where understanding persists and content is regenerated, not the reverse.

## Stack

- **Backend:** FastAPI (Python 3.12 + uv + structlog)
- **Dashboard:** React + Vite (internal observability tool)
- **Database:** Postgres 16 + pgvector + Apache AGE
- **Deploy:** Docker Compose

## Quickstart

```bash
cp .env.example .env
# fill in POSTGRES_PASS and API_KEY

docker compose up --build
```

> First build compiles AGE from source — takes ~3 minutes.

- API: http://localhost:5111/health
- Dashboard: http://localhost:5311

## Development (without Docker)

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --port 5111 --reload

# Dashboard
cd dashboard
npm install
npm run dev   # proxies /api and /ws to :5111
```

## Architecture

See [docs/architecture/overview.md](docs/architecture/overview.md).

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Status + DB check |
| GET | `/api/topics` | List all topics |
| POST | `/api/topics` | Create topic `{ key, value }` |
| WS | `/ws/events` | Live event stream (dashboard) |

Auth: `Authorization: Bearer <API_KEY>` or `?api_key=<key>`. Disabled when `API_KEY` is empty.
