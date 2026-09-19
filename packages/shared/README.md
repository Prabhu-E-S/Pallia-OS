# @pallia/shared

Shared domain vocabulary for Pallia OS.

During Phase 1 this package holds the canonical **enum values** that both the
API and the web app care about. The authoritative source of truth is the Python
backend (`apps/api/app/models/enums.py`); `src/domain/enums.ts` mirrors it so
filters, labels and type unions can be derived from one list in TypeScript.

## Contents

- `src/domain/enums.ts` — string unions (`PatientStatus`, `VisitStatus`,
  `CareTaskStatus`, `ObservationType`, user roles, goal statuses…).

## Usage

This is a plain TypeScript package with a source entry point (`"main"` points
at `src/index.ts`). It is not wired into a bundler in Phase 1; import the file
directly where needed:

```ts
import { VISIT_STATUSES, type VisitStatus } from "@pallia/shared/src/domain/enums";
```

## Keeping it in sync

- Backend enums: `apps/api/app/models/enums.py`
- Frontend mirror (hand-written API types): `apps/web/lib/api/types.ts`
- Shared unions: `packages/shared/src/domain/enums.ts`

All three live in one repo and are intended to be reconciled by a small
code-generation step in a later phase. Until then: change the backend enum,
then update these two mirrors.