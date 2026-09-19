# Development

Everything you need to run Pallia OS locally on this machine (Windows).

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Postgres)
- [Python 3.12+](https://www.python.org/downloads/) on PATH
- [Node.js 20.9+](https://nodejs.org/) (Next.js 16)
- Git (recommended, but the API itself is git-agnostic)

## One-time setup

```bash
# copy environment, adjust to taste
copy .env.example .env            # PowerShell: Copy-Item
```

The `.env` values already reflect this machine's ports (see the comments in
the file). Then:

### 1. Start PostgreSQL

```bash
make infra-up
```

Postgres publishes on **`localhost:55432`** (`POSTGRES_PORT` in `.env`); the
default `5432` is taken by a Windows-native install. Container health check:
`docker compose ps`.

### 2. Backend

```bash
cd apps/api

python -m venv .venv
.venv\Scripts\activate          # PowerShell
pip install -r requirements.txt

alembic upgrade head            # create schema
python -m app.seed              # demo data
uvicorn app.main:app --reload   # http://localhost:8001
```

Docs: Swagger UI at `http://localhost:8001/docs`, ReDoc at `/redoc`.
Health: `GET http://localhost:8001/health`.

### 3. Frontend

```bash
cd apps/web
npm install
npm run dev                     # http://localhost:3000
```

`apps/web/.env.local` sets `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`
(pointing at the API on port 8001). API CORS already allows `localhost:3000`.

## Logging in

Open `http://localhost:3000`, sign in with any seed user and the shared demo
password `pallia123`.

Organization **A — Maple Grove Home Care** (`@pallia.demo`):

| Email                    | Name              | Role             |
| ------------------------ | ----------------- | ---------------- |
| `admin@pallia.demo`      | Ananya Sharma     | ADMIN            |
| `coordinator@pallia.demo`| Ravi Iyer         | CARE_COORDINATOR |
| `nurse@pallia.demo`      | Meera Nair        | NURSE            |
| `nurse2@pallia.demo`     | Kiran Menon       | NURSE            |
| `doctor@pallia.demo`     | Dr. Lakshmi Rao   | DOCTOR           |
| `caregiver@pallia.demo`  | Priya Verma       | CAREGIVER        |
| `patient@pallia.demo`    | Lakshmi Devi      | PATIENT          |

Organization **B — Willow Creek Hospice** (`@willowcreek.demo`):

| Email                     | Name                   | Role             |
| ------------------------- | ---------------------- | ---------------- |
| `admin@willowcreek.demo`  | (seed)                 | ADMIN            |
| `nurse@willowcreek.demo`  | (seed)                 | NURSE            |
| `caregiver@willowcreek.demo` | (seed)               | CAREGIVER        |
| `patient@willowcreek.demo`| (seed)                 | PATIENT          |

Auth is real in Phase 2: passwords are Argon2id-hashed, login is rate limited,
and sessions are recorded in `auth_sessions`. `dev-login` (email-only) still
works in development.

## Everyday commands

```bash
make api              # uvicorn --reload on 8001 (requires venv active)
make web              # npm run dev
make migrate          # alembic upgrade head
make new-migration MESSAGE="add_x"
make seed             # idempotent demo data
make test             # pytest + vitest
make test-api         # pytest
make test-web         # vitest
make typecheck        # tsc --noEmit (web)
make lint-web         # eslint (web)
make format           # ruff format (api)
```

> `make` on Windows: Git for Windows ships `make.exe`; alternatively run the
> underlying commands directly (shown above and in the Makefile).

## Quality gates

- **API**: `ruff check .` and `ruff format .`; `python -m pytest` (Vitest
  suite lives in `apps/api/tests`).
- **Web**: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`.

Keep all four green before finishing a change.

## Project structure

See [architecture.md](architecture.md) for the layout, layering and data flow.

## API surface

Authoritative list — inspect `GET /openapi.json` on the running API for the
full set.

```
POST /api/v1/auth/login      email + password → access token + refresh cookie
POST /api/v1/auth/refresh    rotate refresh session (cookie or body)
POST /api/v1/auth/logout     revoke session, clear cookie
GET  /api/v1/auth/me         current user + organization + permissions
POST /api/v1/auth/dev-login  dev-only: email → token (ENVIRONMENT=development)

GET  /api/v1/dashboard/summary   patients/care-plan/today-visits/open-task counts + lists

GET/POST /api/v1/patients                 list (status/query) · create
GET/PATCH /api/v1/patients/{patient_id}   detail · update
GET       /api/v1/patients/{patient_id}/timeline          timeline events (?kind=…)
GET       /api/v1/patients/{patient_id}/care-team         care team members
GET/PUT   /api/v1/patients/{patient_id}/care-plan         care plan (update status/summary)
POST      /api/v1/patients/{patient_id}/care-plan/goals   add a care goal
PATCH     /api/v1/patients/{patient_id}/care-plan/goals/{goal_id}   goal status/priority
GET/POST  /api/v1/patients/{patient_id}/observations      patient observations
GET       /api/v1/patients/{patient_id}/observations/recent   "what changed?" comparisons
POST      /api/v1/patients/{patient_id}/observations/confirm   confirm reviewed observations
GET/POST  /api/v1/patients/{patient_id}/visits            patient visits
GET/POST  /api/v1/patients/{patient_id}/tasks             patient care tasks
GET/POST  /api/v1/patients/{patient_id}/caregiver-reports          reports · create
PATCH     /api/v1/patients/{patient_id}/caregiver-reports/{id}     update (transcript/notes)
POST      /api/v1/patients/{patient_id}/caregiver-reports/{id}/cancel  cancel a report
POST      /api/v1/patients/{patient_id}/voice/transcribe   audio → transcript (multipart)
POST      /api/v1/patients/{patient_id}/voice/extract      transcript → draft observations

GET/POST /api/v1/observations        observations (org-wide) · record
GET/POST /api/v1/visits              visits (future/past/status) · create
GET/PATCH /api/v1/visits/{visit_id}  visit detail · update (status/notes)

GET/POST /api/v1/tasks               tasks (filters) · create
GET/PATCH /api/v1/tasks/{task_id}    task detail · update (status/assignee/…)
POST /api/v1/tasks/{task_id}/assign  assign a task

GET/POST /api/v1/users               users · create
GET       /api/v1/organizations      organizations
```

### Caregiver reports & voice (Phase 3)

The `VOICE` flow: create a report → `POST .../voice/transcribe` (audio upload)
→ `POST .../voice/extract` → review the draft → `POST .../observations/confirm`.
Manual modes (`QUICK_STATUS`, `STRUCTURED`, `TEXT`) create confirmed
observations in one step. Everything stays scoped: a `CAREGIVER` only touches
their linked patients, and staff are org-wide.

Provider-driven seams (`ENVIRONMENT=development` defaults in `app/core/config.py`):

- `SPEECH_PROVIDER=local` — treats the "audio" upload as UTF-8 text (offline
  testing); `openai` lazily pulls in Whisper and returns 503
  (`VOICE_SERVICE_UNAVAILABLE`) when `openai` isn't installed.
- `AI_PROVIDER=local` — deterministic rule-based extraction; `openai` uses a
  lazily-imported chat model (missing dependency → 503 `AI_SERVICE_UNAVAILABLE`,
  extraction failure → 422 `AI_EXTRACTION_FAILED`).

The extraction prompt (`v1`) explicitly forbids inventing values: anything the
caregiver didn't say stays `not_mentioned`, and ambiguous phrasing keeps
`value: null`. Confirmed observations are linked back to the source report
(`source_reference`) with `ai_generated` / `human_verified` / `confidence` /
`model_version` metadata.

> Everything under `/api/v1` except `auth/login`, `auth/refresh` and
> `auth/dev-login` requires `Authorization: Bearer <access token>`. Lists and
> single-resource reads are scoped to the caller: staff see their whole
> organization, `CAREGIVER` sees only linked patients, `PATIENT` sees their
> own record (out-of-scope IDs return 404).

> Roadmap routes live in the models but are not yet exposed: `alerts`,
> `communications`, and full `care-teams` CRUD are later phases.

## Troubleshooting

- **Port 8000 in use** (Windows Docker / WSL proxy): the API defaults to
  `API_PORT=8001` locally; change `apps/api/.env` or `run_api` accordingly.
- **`docker compose ps` shows postgres unhealthy**: wait ~10s and retry; first
  image pull takes a while.
- **Frontend timezone off-by-one**: the API stores UTC; the UI renders in the
  browser's local zone, so dates shift around midnight — expected.
- **Web can't reach API (CORS / fetch error)**: confirm API is on 8001 and
  `NEXT_PUBLIC_API_BASE_URL` in `apps/web/.env.local` matches. Preflight
  `OPTIONS` responses echo `Access-Control-Allow-Origin: http://localhost:3000`.

## Seams for later phases

- Swap the password login flow for a real OIDC provider without touching most
  of the UI — `AuthProvider` already treats login as "get a token + user", and
  the refresh cookie wrapper is isolated in the API client.
- Move role→permission mapping from code constants
  (`app/core/permissions.py`) into a per-user/permission table.
- Move login rate limiting from the in-memory limiter to a shared store
  (Redis) once more than one API instance runs.
- Introduce `Row Level Security` in Postgres for defense-in-depth beyond the
  service-layer scoping.