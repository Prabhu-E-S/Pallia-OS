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

Open `http://localhost:3000`, click **Sign in** and use any seed user (the
dev-login button fills the admin automatically):

| Email                    | Name              | Role             |
| ------------------------ | ----------------- | ---------------- |
| `admin@pallia.demo`      | Ananya Sharma     | ADMIN            |
| `coordinator@pallia.demo`| Ravi Iyer         | CARE_COORDINATOR |
| `nurse@pallia.demo`      | Meera Nair        | NURSE            |
| `nurse2@pallia.demo`     | Kiran Menon       | NURSE            |
| `doctor@pallia.demo`     | Dr. Lakshmi Rao   | DOCTOR           |
| `caregiver@pallia.demo`  | Priya Verma       | CAREGIVER        |

The seed users have no passwords in Phase 1 — auth is a development-only
email exchange (`POST /api/v1/auth/dev-login`) that issues a signed bearer
token, valid for 12 hours.

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

## API surface (Phase 1)

Authoritative list — inspect `GET /openapi.json` on the running API for the
full set.

```
POST /api/v1/auth/dev-login   exchange seed user email for a bearer token
GET  /api/v1/auth/me          current user + organization

GET  /api/v1/dashboard/summary   patients/care-plan/today-visits/open-task counts + lists

GET/POST /api/v1/patients                 list (status/query) · create
GET/PATCH /api/v1/patients/{patient_id}   detail · update
GET       /api/v1/patients/{patient_id}/timeline         timeline events
GET       /api/v1/patients/{patient_id}/care-team        care team members
GET/PUT   /api/v1/patients/{patient_id}/care-plan        care plan + goals
GET/POST  /api/v1/patients/{patient_id}/observations     patient observations
GET/POST  /api/v1/patients/{patient_id}/visits           patient visits
GET/POST  /api/v1/patients/{patient_id}/tasks            patient care tasks

GET/POST /api/v1/observations        observations (org-wide) · record
GET/POST /api/v1/visits              visits (future/past/status) · create
GET/PATCH /api/v1/visits/{visit_id}  visit detail · update (status/notes)

GET/POST /api/v1/tasks               tasks (filters) · create
GET/PATCH /api/v1/tasks/{task_id}    task detail · update (status/assignee/…)
POST /api/v1/tasks/{task_id}/assign  assign a task

GET/POST /api/v1/users               users · create
GET       /api/v1/organizations      organizations
```

> Roadmap routes live in the models but are not yet exposed: `alerts`,
> `communications`, and full `care-teams` CRUD are Phase 2.

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

- Swap `dev-login` for a real OIDC provider without touching the UI
  (`apps/web/components/providers/auth-provider.tsx` wraps whatever issues
  the token).
- Move role→permission mapping from code constants
  (`app/core/permissions.py`) into a per-user table.
- Introduce `Row Level Security` in Postgres for defense-in-depth beyond the
  service-layer scoping.