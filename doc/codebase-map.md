# Codebase Map

Snapshot doc for agent orientation. Use this to avoid blind repo-wide
searching. If this file conflicts with the code, trust the code and refresh
this file.

## Last Verified

- Date: 2026-05-16
- Verified areas:
  - top-level repo layout
  - backend implemented routes and service areas
  - DB schema and migration presence
  - frontend page structure and API client surface
  - task progress snapshot
- Confidence:
  - high for auth, sync, ontology, analytics, anomalies, exports, refresh, and dashboard shell areas
  - medium for insight-generation depth without a deeper behavior review
  - high for progress docs

## Read This After

1. [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md)
2. [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/QUICKSTART.md)
3. [`doc/README.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/README.md)

`ARCHITECTURE.md` explains the architectural source of truth.
This file explains what is currently built and where to look first.

## Repo Shape

Top-level folders:

- `apps/backend`: FastAPI backend
- `apps/frontend`: Next.js frontend
- `packages`: shared-package placeholder area, currently light usage
- `doc`: documentation index, versioned plans/design docs, task breakdowns
- `infra`: infra placeholder area, currently light usage

Top-level docs:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md): system source of truth
- [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md): visual design source of truth
- [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/QUICKSTART.md): setup, run, test, lint
- [`doc/README.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/README.md): docs index
- [`doc/tasks/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/progress.md): task index for the versioned trackers
- [`doc/v2/plan.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/v2/plan.md): active post-v1 planning entrypoint

## Current Delivery State

Implemented and verified:

- backend auth flow (login, logout, session, JWT/session handling)
- backend health endpoint
- backend source sync (6 entity readers, snapshot persistence, orchestration)
- backend ontology mapping (domain types, 6 mappers, attribution resolver, persistence, orchestrator)
- backend analytics aggregation and dashboard read-model queries
- backend anomaly detection rules and persistence
- backend export payload assembly and workbook generation
- backend refresh trigger, job/status flow, and orchestration entrypoints
- backend insight-generation entrypoints and service surface
- frontend login flow
- frontend dashboard UI shells, cards, tables, charts, and refresh widgets
- frontend tests for auth/dashboard components and flows

Still worth checking for product depth, not for module existence:

- insight-generation quality and prompt design
- export workbook breadth versus product expectations
- refresh orchestration production-hardening assumptions
- shared `packages/*`
- `infra/`

Practical summary:

- backend has real auth, sync, ontology, analytics, anomaly, export, refresh, and API modules
- insight generation is present and wired, but should still be reviewed for product depth when behavior changes
- frontend and backend are both present as the completed v1 baseline

## Backend Map

Entrypoint:

- [`apps/backend/app.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/app.py): FastAPI app factory, middleware, exception handling, router registration

Implemented backend areas:

- [`apps/backend/common`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/common): config, DB wiring, error classes, clock, logging
- [`apps/backend/auth`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth): domain, repository, password hashing, JWT/session service, ORM user model
- [`apps/backend/api`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api): health/auth/dashboard/departments/claims/anomalies/exports/refresh routes, request/response schemas, auth dependency
- [`apps/backend/sync`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync): 6 source readers, snapshot repository, sync orchestrator, source DB wiring
- [`apps/backend/ontology`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology): domain types, mappers, attribution resolver, ontology repository, orchestrator
- [`apps/backend/analytics`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/analytics): aggregate reads, rankings, deltas, departments, repositories
- [`apps/backend/anomalies`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/anomalies): anomaly rules, repository, list/detail mapping
- [`apps/backend/insights`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/insights): domain, service, generation entrypoints
- [`apps/backend/exports`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/exports): workbook build and export payload composition
- [`apps/backend/refresh`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/refresh): trigger, status, job reads, orchestration entrypoints

Current DB models:

- [`apps/backend/auth/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth/schema.py): `users`
- [`apps/backend/sync/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/schema.py): source snapshot tables
- [`apps/backend/ontology/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/schema.py): ontology and unresolved mapping tables
- analytics, anomalies, refresh, and related modules have supporting persistence and repositories in their own areas

Source-side models (separate read-only base):

- [`apps/backend/sync/readers/_source_models.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/readers/_source_models.py): `departments`, `employees`, `claims`, `payroll`, `cost_centers`, `budget_codes`

Migration system:

- Alembic is installed and configured in `apps/backend/alembic/`
- initial migration exists under `alembic/versions/`
- run with `alembic upgrade head`

## Backend Routes

Implemented routes include:

- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/trends`
- `GET /api/dashboard/top-departments`
- `GET /api/dashboard/claim-types`
- `GET /api/departments`
- `GET /api/departments/{id}`
- `GET /api/departments/{id}/trends`
- `GET /api/departments/{id}/employees`
- `GET /api/departments/{id}/claim-types`
- `GET /api/departments/{id}/claims`
- `GET /api/claims`
- `GET /api/anomalies`
- `GET /api/anomalies/{id}`
- `POST /api/exports/executive-summary`
- `POST /api/refresh`
- `GET /api/refresh/status`
- `GET /api/refresh/jobs/{id}`

Main files:

- [`apps/backend/api/routes/health.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/health.py)
- [`apps/backend/api/routes/auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/auth.py)
- [`apps/backend/api/routes/dashboard.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/dashboard.py)
- [`apps/backend/api/routes/departments.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/departments.py)
- [`apps/backend/api/routes/claims.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/claims.py)
- [`apps/backend/api/routes/anomalies.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/anomalies.py)
- [`apps/backend/api/routes/exports.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/exports.py)
- [`apps/backend/api/routes/refresh.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/refresh.py)

## Frontend Map

Frontend app root:

- [`apps/frontend/src/app`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/app)

Main routes:

- `/` -> redirects to `/dashboard`
- `/login`
- `/dashboard`
- `/dashboard/anomalies`
- `/dashboard/departments/[id]`

First places to inspect:

- [`apps/frontend/src/app/login/page.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/app/login/page.tsx)
- [`apps/frontend/src/app/dashboard/page.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/app/dashboard/page.tsx)
- [`apps/frontend/src/components/dashboard/dashboard-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/dashboard-shell.tsx)
- [`apps/frontend/src/components/dashboard/anomalies-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/anomalies-shell.tsx)
- [`apps/frontend/src/components/dashboard/department-detail-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/department-detail-shell.tsx)

Supporting areas:

- [`apps/frontend/src/components/auth`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/auth)
- [`apps/frontend/src/components/shared`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/shared)
- [`apps/frontend/src/lib/api`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/api)
- [`apps/frontend/src/lib/mappers.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/mappers.ts)
- [`apps/frontend/src/lib/formatters.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/formatters.ts)

## Frontend-Backend Shape

Main current seam to verify before deeper work:

- whether current dashboard, anomaly, export, refresh, and insight behavior is product-complete enough for v2 goals
- whether the code matches the completed task checklists at product depth, not only module existence

## Tests Map

Backend tests:

- [`apps/backend/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit)
- [`apps/backend/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration)

Frontend tests:

- [`apps/frontend/src/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/unit)
- [`apps/frontend/src/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration)

## Progress Snapshot

From [`doc/tasks/v1/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/v1/progress.md):

- done: project bootstrap
- done: auth
- done: frontend dashboard
- done: api
- done: source sync
- done: ontology mapping
- done: analytics aggregation
- done: anomaly detection
- done: insight generation
- done: refresh orchestration
- done: reporting and export
- done: data store
- done: quality gates and CI

Separate versioned trackers:

- [`doc/tasks/v2/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/v2/progress.md): v2 dashboard shell and navigation work
- [`doc/tasks/v3/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/v3/progress.md): v3 ingestion and cleaning work
- [`doc/tasks/v4/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/v4/progress.md): v4 workspace and dataset work

## Known Drift Hotspots

Verify these before trusting the snapshot:

- route inventory under `apps/backend/api/routes/`
- frontend API client expectations under `apps/frontend/src/lib/api/`
- whether v2 planning assumptions still match the completed v1 code
- package versions

## Refresh Rules

Refresh this file when:

- a new route group is added or removed
- a major module changes status materially
- a v2 scope decision changes the most important repo entrypoints
- the task progress doc changes materially

Do not update this file for small internal refactors that do not change
navigation or module status.
