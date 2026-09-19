# Pallia OS

Calm, minimal, enterprise-grade software for **home-based palliative care** —
coordination software for clinicians, care coordinators and families that
stays out of the way during the hardest moments.

This monorepo contains the Phase 1 **product foundation**: tenants, identities,
patients, care teams, care plans, observations, visits, tasks, communications,
timeline and alerts — as a clean, typed, fully-tested vertical slice.

> **Phase 1 scope note** — no AI, no clinical decision support, no external OS
> integration. Those are later phases with their own seams.

## Stack

| Layer     | Technology                                              |
| --------- | ------------------------------------------------------- |
| Frontend  | Next.js 16 (App Router), React, TypeScript, Tailwind v4 |
| Backend   | FastAPI, SQLAlchemy 2.0, Pydantic v2, Python 3.12       |
| Database  | PostgreSQL 16, Alembic                                  |
| Tooling   | Docker Compose, Makefile, ruff, pytest, Vitest, ESLint |

## Quick start

```bash
copy .env.example .env          # PowerShell
make infra-up                   # docker compose up -d postgres
make api                        # uvicorn on http://localhost:8001 (venv activated)
make web                        # Next.js on http://localhost:3000
```

Then open **http://localhost:3000**, sign in with `admin@pallia.demo` (or any
seed user, e.g. `nurse@pallia.demo`), and explore.

The API needs a database first:

```bash
cd apps/api
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head           # create schema
python -m app.seed             # load demo data
```

> Local ports deviate from defaults because Windows services already occupy
> them: Postgres → **55432**, API → **8001**. See `.env` / `.env.example`.

## Documentation

- [Architecture](docs/architecture.md) — system overview, layering, authN/Z
- [Database](docs/database.md) — schema, multitenancy, seed data
- [Development](docs/development.md) — full setup, commands, API surface,
  troubleshooting

## Repository layout

```
apps/
  api/      FastAPI backend (core/, models/, schemas/, services/, api/routes/)
  web/      Next.js frontend (app/, components/, lib/)
packages/
  shared/   TS mirror of shared domain enums
infrastructure/
  docker/   supplementary docker docs
docs/       architecture / database / development
docker-compose.yml   postgres + api + web
Makefile             dev command shortcuts
.env.example         documented environment defaults
```

## Project conventions

- UTC everywhere in the API; the UI renders local time.
- Auth is development-only in Phase 1 — the login screen exchanges a seed
  user's email for a signed bearer token (the seam for OIDC later).
- All API errors use a single envelope
  (`{ "error": { "code", "message", "details" } }`).
- No `git` commands run inside this workspace; versioning is left to the
  owning team.

## Status

Everything is in place and verified locally: schema + migrations + seed, API
route suite (12 passing), web build/typecheck/lint (clean) and Vitest (17
passing), plus end-to-end smoke tests against the live API and CORS between
the two processes.

Demo credentials: any seed email — see [Development](docs/development.md#logging-in).