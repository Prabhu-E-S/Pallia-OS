# Docker infrastructure

The primary infrastructure file is the project-level `docker-compose.yml` at
the repository root. This directory holds supplementary Docker files.

## Services (root `docker-compose.yml`)

| Service   | Image / context       | Host port                 | Purpose                          |
| --------- | --------------------- | ------------------------- | -------------------------------- |
| postgres  | `postgres:16-alpine`  | `${POSTGRES_PORT:-5432}`  | PostgreSQL 16 database           |
| api       | `./apps/api` (python:3.12-slim) | `${API_PORT:-8000}` | FastAPI backend, `alembic upgrade head` then seed then uvicorn |
| web       | `./apps/web` (Node 22-alpine, Next.js) | `${WEB_PORT:-3000}` | Next.js frontend (production server) |

## Local development ports on this machine

`POSTGRES_PORT` is published as **55432** (a Windows-native PostgreSQL already
owns the default `5432`), and `API_PORT` is **8001** (a leftover Docker/WSL
proxy holds `8000`). Copy the root `.env` values:

```
POSTGRES_PORT=55432   DATABASE_URL=postgresql+psycopg://pallia:pallia@localhost:55432/pallia
API_PORT=8001         NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## Development overrides

For local iteration against a running API, a typical override:

```yaml
# docker-compose.dev.yml (example)
services:
  api:
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```

Apply with `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`.

## Database reset

```bash
# remove the postgres volume (wipes all data, including seeds)
docker compose down -v
docker compose up -d postgres
cd apps/api && alembic upgrade head && python -m app.seed
```

## Health checks

- `postgres` container health is tracked by Compose (`pg_isready`).
- API readiness is exposed at `GET /health` (checks the database too).