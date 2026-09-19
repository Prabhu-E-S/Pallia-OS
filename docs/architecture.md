# Architecture

Pallia OS is a calm, minimal, enterprise-grade operating system for
home-based palliative care: coordination software that stays out of the way
of clinicians and families.

Phase 1 delivers the **product foundation** — tenants, identities, patients,
care teams, care plans, observations, visits, tasks and communications — as a
clean, typed, testable vertical slice. Phase 2 adds **authentication and
authorization**: password login, revocable refresh sessions, centralized RBAC
and object-level row scoping. Phase 3 delivers the **caregiver workflow and
voice-to-care**: caregiver reports, speech-to-text, AI-assisted observation
drafting with mandatory human review, and a filterable timeline with
"what changed?" comparisons. The AI layer is strictly documentation support —
there is **no clinical decision support** and no treatment guidance.

## System overview

```
┌─────────────────┐     HTTPS/JSON      ┌──────────────────────┐
│  Next.js 16 app │ ──────────────────► │  FastAPI (Python 3.12)│
│  apps/web       │   REST /api/v1/*    │  apps/api             │
│  App Router CSR │ ◄────────────────── │  /health              │
│  Tailwind v4 UI │   typed client      │  error envelopes      │
└─────────────────┘                     └──────────┬───────────┘
                                                   │  SQLAlchemy 2.0
                                                   ▼
                                         ┌──────────────────────┐
                                         │ PostgreSQL 16        │
                                         │ tenant columns + row  │
                                         │ security filtering    │
                                         └──────────────────────┘
```

- **Web** is a client-side data app: every page fetches from the API in
  `useEffect` (no server-side data fetching), so static builds stay simple and
  the API remains the single source of truth.
- **API** owns authentication, authorization, tenant scoping and all database
  writes; every public endpoint verifies a signed bearer token and an
  organization boundary.
- **Postgres** is single-database, multi-tenant (see
  [databases.md](databases.md)).

## Repository layout

```
pallia-os/
├── docker-compose.yml          # postgres + api + web services
├── Makefile                    # dev commands (up/down/migrate/seed/test…)
├── .env.example                # documented environment defaults
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/           # config, db session, errors, security, permissions
│   │   │   ├── models/         # SQLAlchemy 2.0 ORM models (+ domain enums)
│   │   │   ├── schemas/        # Pydantic request/response models
│   │   │   ├── services/       # org-scoped business logic per aggregate
│   │   │   ├── api/routes/     # FastAPI routers (thin, delegate to services)
│   │   │   └── seed.py         # deterministic demo dataset
│   │   ├── migrations/         # Alembic
│   │   └── tests/              # pytest suite
│   └── web/                    # Next.js frontend
│       ├── app/                # App Router pages (login/dashboard/patients/…)
│       ├── components/         # ui primitives, layout shell, providers
│       └── lib/                # typed API client, session, format helpers
├── packages/shared/            # shared domain enums (TS mirror of backend)
├── infrastructure/docker/      # supplementary docker documentation
└── docs/                       # this documentation
```

No Git repository is initialized in this workspace — the tree is meant to be
reviewed and versioned by the owning team.

## Backend layering

1. **Routes** (`app/api/routes/`) — HTTP in/out only: path params, query
   params, request bodies, `response_model`. Auth is enforced via
   `Depends(get_current_user)` and `Depends(require_permission(...))`.
2. **Services** (`app/services/`) — business logic and the place where every
   query/statement scopes rows by `organization_id` and, where relevant,
   `patient_id`. Services record audit events through the shared audit helper.
3. **Models / Schemas** — database identity (`app/models/`) and API
   contracts (`app/schemas/`) are separate layers; schemas are never reused as
   query objects.

Every request flow: route → dependency (authn/authz) → service (scoped read /
write) → response model → JSON.

### Request lifecycle example

```
PATCH /api/v1/tasks/{id}
  → get_current_user (decodes HMAC bearer; validates sid session if present)
  → require_permission("care_task.update", "care_task.assign")
  → tasks.update_task(db, actor, task_id, payload)
      - resolves task by id + organization_id == actor.organization_id
      - if actor is CAREGIVER, node must belong to one of their linked patients
        (else NOT_FOUND)
      - applies allowed transitions, sets completed_at
      - writes AuditLog row
  → CareTaskOut
```

## Authentication

- **Login**: `POST /api/v1/auth/login` takes an email + password, verifies
  against the Argon2id hash, and returns a 30-minute access token plus an
  HttpOnly refresh cookie (`pallia_refresh`).
- **Passwords**: hashed with Argon2id (`argon2-cffi`); a PBKDF2-HMAC fallback
  verifies legacy hashes. Seed users share the demo password `pallia123`.
- **Access tokens**: HMAC-signed, 30 min expiry, carry an optional `sid`
  (session id) claim. Not persisted — the web app holds them in JS memory only.
- **Refresh sessions**: one row per session in `auth_sessions` (SHA-256 token
  hash, 7-day lifetime, revocable). Every `/auth/refresh` rotates the session
  and issues a new cookie; logout revokes it; `get_current_user` validates the
  session when a `sid` is present.
- **Rate limiting**: in-memory sliding window (10 attempts / 15 min per
  email+IP) on login (`app/core/rate_limit.py`).
- **Development**: `dev-login` (email only) still exists behind
  `ENVIRONMENT=development` and follows the same session/cookie flow.
- **The seam for later**: replace the login exchange with OAuth2/OIDC (Auth0,
  Azure AD B2C or similar); the UI only deals with access tokens + the refresh
  cookie.

## Authorization

- Roles: `ADMIN`, `CARE_COORDINATOR`, `NURSE`, `DOCTOR`, `CAREGIVER`,
  `PATIENT`.
- Permissions are flat string capabilities (`patient.read`, `visit.write`, …)
  mapped per role in `app/core/permissions.py`; `require_permission(..., any_of)`
  guards routes. Role→permission mapping can move to a per-user table later
  without touching route code.
- **Object-level scoping** (`app/services/authorization.py`):
  - staff (ADMIN/CARE_COORDINATOR/NURSE/DOCTOR) — org-wide.
  - `CAREGIVER` — only patients linked via `patient_caregivers`.
  - `PATIENT` — only their own record (via `users.patient_id`).
  - List endpoints filter automatically (`where_patient_scope`); detail reads
    call `ensure_patient_access` and return **404** for out-of-scope rows so
    existence is not revealed.

## Caregiver reports & voice-to-care (Phase 3)

Lifecycle of a report: `DRAFT → PROCESSING → REVIEW_REQUIRED → CONFIRMED`,
or `CANCELLED` at any point. Manual modes (`QUICK_STATUS`, `STRUCTURED`,
`TEXT`) are created directly as `CONFIRMED` observations; the `VOICE` mode
starts a draft, transcribes the audio, runs AI extraction, and lands in
`REVIEW_REQUIRED` — a human must confirm before anything enters the record.

- **Speech-to-text** (`app/services/speech/`): the default `local` provider
  treats the upload as UTF-8 text so the pipeline can be tested offline; a
  lazy-loaded OpenAI Whisper integration returns a `VOICE_SERVICE_UNAVAILABLE`
  503 when the dependency is missing.
- **Extraction** (`app/services/ai/`, prompt version `EXTRACTION_PROMPT_VERSION
  = "v1"`): turns a transcript into candidate observations. Missing or
  ambiguous values must stay `not_mentioned` or `null` — the extractor never
  invents numbers. A deterministic `local` rules provider mirrors OpenAI output
  for tests/dev.
- **Human confirmation** is mandatory. `POST .../observations/confirm`
  persists the reviewer-approved items (with per-item `confidence` and a
  source reference to the source report), emits `observation.confirmed` /
  `observation.edited` audit events, and the report moves to `CONFIRMED`.
- **Provenance**: confirmed observations carry `source_reference` (a FK to the
  report), `ai_generated`, `human_verified`, `confidence`, and `model_version`.
  Only `CONFIRMED` reports appear on the patient timeline (kind
  `caregiver_report`).

The web app ships a dedicated **`/care` workspace** for the `CAREGIVER` role
(heads-up list of reports awaiting review, per-patient recent reports, and a
report wizard supporting all four modes with an accessible in-browser voice
recorder and a typed-transcript fallback when transcription is unavailable).

## Errors

All failures return one envelope:

```json
{ "error": { "code": "...", "message": "...", "details": null } }
```

- `VALIDATION_ERROR` (422) — request data invalid; `details` lists
  field-level problems.
- `NOT_FOUND` (404), `UNAUTHORIZED` (401), `FORBIDDEN` (403),
  `RATE_LIMITED` (429 — login throttled), `INTERNAL_ERROR` (500).

Route handlers raise domain exceptions
(`app/core/errors.py`) and the app-level exception handlers translate them to
the envelope — routes never build HTTP responses themselves.

## Frontend architecture (apps/web)

- **Framework**: Next.js 16 App Router with the optional `(app)` route group
  guarded by an auth shell (`components/layout/app-shell.tsx`).
- **Styling**: Tailwind CSS v4 with a small calibrated theme in
  `app/globals.css` — warm neutrals, one teal accent, no dark mode.
- **Data access**: typed client in `lib/api/` (mirrors of backend schemas,
  one module per aggregate), error-via-`ApiErrorResponse` matching the backend
  envelope. Pages fetch in effects; no TanStack Query in Phase 1 (data volumes
  are tiny and refetching is explicit).
- **State**: `AuthProvider` (context) is the only global state; it restores
  the session on bootstrap (`/auth/me`, falling back to `/auth/refresh`),
  holds permissions, and exposes `hasPermission`/`canAccess`. Everything else
  is local component state. The API client attaches the in-memory bearer
  token, sends `credentials: "include"`, and silently refreshes once on 401.
- **Testing**: Vitest + React Testing Library for helpers, badge/status
  mappings, UI primitives, the API client's refresh-on-401 behavior, and auth
  provider bootstrap/login/logout; `npm run typecheck`/`build` gate quality.

## Cross-cutting decisions

- **No Git commands** are run in this workspace by design.
- **Time zones**: API stores UTC (`aware datetimes`); the web app renders in
  the browser's local zone.
- **Tenant safety**: services always filter by the actor's
  `organization_id`; there is no way to query another tenant's rows at the
  service layer. Object-level rules further narrow caregiver/patient access.
- **Seeding**: `python -m app.seed` is idempotent per organization and
  produces a consistent demo set — **Maple Grove Home Care** (6 patients,
  full team, plus PATIENT + CAREGIVER accounts) and **Willow Creek Hospice**
  (3 patients, minimal team) — with care teams, observations, visits, tasks,
  timeline, alerts and (Phase 3) caregiver reports for the UI. Every demo
  account uses the shared password `pallia123`.
- **Expansion seams** (later phases): drug/medication scheduling, alerts &
  notifications, consent lifecycles, reporting, and richer AI copilots (real
  Whisper transcription and an LLM extraction provider are already pluggable
  behind the Phase 3 provider seams).