# Pallia OS

Calm, minimal, enterprise-grade software for **home-based palliative care** —
coordination software for clinicians, care coordinators and families that
stays out of the way during the hardest moments.

This monorepo delivers the **product foundation** — tenants, identities,
patients, care teams, care plans, observations, visits, tasks, communications,
timeline and alerts — as a clean, typed, fully-tested vertical slice, plus
Phase 2 **authentication and authorization**: real password login (Argon2id),
revocable refresh sessions, centralized RBAC, and object-level row scoping
(caregiver ↔ linked patients, patient ↔ own record).

Phase 3 adds the **caregiver workflow and voice-to-care**: a caregiver home
workspace with quick/structured/text/voice reports, speech-to-text
transcription (*voices become text — never clinical data*), AI-assisted
drafting of observations from the transcript, a human review/confirm step, and
a filtered patient timeline with "what changed?" comparisons. The AI only
*assists documentation under human confirmation* — it never forms or overrides
a clinical decision.

> **Scope note** — no clinical decision support, no treatment guidance, no
> external OS integration. Voice handling and AI extraction are provider-based
> seams with deterministic local fallbacks for development.

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

Then open **http://localhost:3000**, sign in with
`admin@pallia.demo` / `pallia123` (any seed user shares the demo password;
see the login screen for full list), and explore.

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
- Authentication: password login (Argon2id hashing with PBKDF2 fallback),
  short-lived access tokens (30 min, JS memory only) behind an HttpOnly
  `SameSite=Lax` refresh cookie that is rotated on every use. Refresh
  sessions are revocable (logout / suspension) and rate-limited (10 tries /
  15 min per email+IP). A development-only `dev-login` (email only, no
  password) survives behind `ENVIRONMENT=development` for convenience.
- Authorization: flat string permissions per role in `app/core/permissions.py`;
  staff are org-wide, `CAREGIVER` sees only linked patients, `PATIENT` sees
  only their own record. Cross-scope reads return 404 (don't reveal existence).
- All API errors use a single envelope
  (`{ "error": { "code", "message", "details" } }`).
- No `git` commands run inside this workspace; versioning is left to the
  owning team.

## Status

Verified locally: schema + migrations + seed (2 demo organizations), API
route suite (84 passing), web build/typecheck/lint (clean) and Vitest (30
passing), plus end-to-end smoke tests against the live API: login/refresh/
logout with cookie rotation, cross-tenant 404 isolation, caregiver and
patient row scoping, career-plan/goal updates, caregiver report lifecycle
(draft → transcribe → extract → review → confirm), and CORS between the two
processes.

Demo credentials: any seed email, password `pallia123` — see
[Development](docs/development.md#logging-in).