# Architecture

Pallia OS is a calm, minimal, enterprise-grade operating system for
home-based palliative care: coordination software that stays out of the way
of clinicians and families.

Phase 1 delivers the **product foundation** — tenants, identities, patients,
care teams, care plans, observations, visits, tasks and communications — as a
clean, typed, testable vertical slice. There is deliberately **no AI**, no
clinical decision support, and no external OS integration in Phase 1.

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
  → get_current_user (decodes HMAC bearer → User)
  → require_permission("task.write")
  → tasks.update_task(db, actor, task_id, payload)
      - resolves task by id + organization_id == actor.organization_id
      - applies allowed transitions, sets completed_at
      - writes AuditLog row
  → CareTaskOut
```

## Authentication

- **Phase 1 development login**: `POST /api/v1/auth/dev-login` exchanges any
  seed user's email for a signed bearer token. Programmatic and UI flows call
  it; it is disabled unless `ENVIRONMENT=development`.
- **Tokens**: HMAC-signed, 12h expiry, no JWT dependency.
- **Session in the web app**: token + user profile persisted to
  `localStorage`; the API client attaches `Authorization: Bearer …`.
- **The seam for later**: replace dev-login with OAuth2/OIDC (Auth0, Azure AD
  B2C or similar). Nothing in the UI assumes passwords exist.

## Authorization

- Roles: `ADMIN`, `CARE_COORDINATOR`, `NURSE`, `DOCTOR`, `CAREGIVER`.
- Permissions are flat string capabilities (`patient.read`, `visit.write`, …)
  mapped per role in `app/core/permissions.py`.
- `require_permission(*perms, any_of=False)` guards routes; role→permission
  mapping can be replaced by a per-user/permission table in a later phase
  without touching route code (the dependency resolves permissions from the
  user object).

## Errors

All failures return one envelope:

```json
{ "error": { "code": "...", "message": "...", "details": null } }
```

- `VALIDATION_ERROR` (422) — request data invalid; `details` lists
  field-level problems.
- `NOT_FOUND` (404), `UNAUTHORIZED` (401), `FORBIDDEN` (403),
  `INTERNAL_ERROR` (500).

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
- **State**: `AuthProvider` (context) is the only global state; everything
  else is local component state.
- **Testing**: Vitest + React Testing Library for helpers, badge/status
  mappings, and UI primitives; `npm run typecheck`/`build` gate quality.

## Cross-cutting decisions

- **No Git commands** are run in this workspace by design.
- **Time zones**: API stores UTC (`aware datetimes`); the web app renders in
  the browser's local zone.
- **Tenant safety**: services always filter by the actor's
  `organization_id`; there is no way to query another tenant's rows at the
  service layer.
- **Seeding**: `python -m app.seed` is idempotent per organization and
  produces a consistent demo set (6 patients, care teams, observations,
  visits, tasks, timeline, alerts) used by the UI.
- **Expansion seams** (later phases): drug/medication scheduling, alerts &
  notifications, consent lifecycles, reporting, and the AI-supported care
  copilot — none are included in Phase 1.