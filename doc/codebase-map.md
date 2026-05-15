# Codebase Map

Snapshot doc for agent orientation. Use this to avoid blind repo-wide searching.
If this file conflicts with the code, trust the code and refresh this file.

## Last Verified

- Date: 2026-05-15
- Verified areas:
  - top-level repo layout
  - backend implemented routes and auth module
  - frontend page structure and API client surface
  - task progress snapshot
- Confidence:
  - high for auth and dashboard areas
  - medium for placeholder modules and progress docs

## Read This After

1. [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md)
2. [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/QUICKSTART.md)

`ARCHITECTURE.md` explains what the system should be.
This file explains what is currently built and where to look first.

## Repo Shape

Top-level folders:

- `apps/backend`: FastAPI backend
- `apps/frontend`: Next.js frontend
- `packages`: shared-package placeholder area, currently empty
- `doc`: proposal, design docs, task breakdowns
- `infra`: infra placeholder area, currently empty

Top-level docs:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md): system source of truth
- [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md): visual design source of truth
- [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/QUICKSTART.md): setup, run, test, lint
- [`doc/tasks/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/progress.md): module completion checklist

## Current Delivery State

Implemented enough to use:

- backend auth flow
- backend health endpoint
- frontend login flow
- frontend dashboard UI shells, cards, tables, charts, and refresh widgets
- frontend tests for auth/dashboard components and flows
- backend tests for auth and health

Mostly placeholders:

- source sync
- ontology mapping
- analytics aggregation
- anomaly detection backend
- insight generation backend
- export backend
- refresh orchestration backend
- shared `packages/*`
- `infra/`

Practical summary:

- backend is only real in auth + health
- frontend is ahead of backend and already expects dashboard APIs that do not exist yet

## Backend Map

Entrypoint:

- [`apps/backend/app.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/app.py): FastAPI app factory, middleware, exception handling, router registration

Implemented backend areas:

- [`apps/backend/common`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/common): config, DB wiring, error classes, clock, logging
- [`apps/backend/auth`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth): domain, repository, password hashing, JWT/session service, ORM user model
- [`apps/backend/api`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api): health/auth routes, request/response schemas, auth dependency

Backend modules not yet implemented:

- `apps/backend/sync`
- `apps/backend/ontology`
- `apps/backend/analytics`
- `apps/backend/anomalies`
- `apps/backend/insights`
- `apps/backend/exports`
- `apps/backend/refresh`

Only current DB model:

- [`apps/backend/auth/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth/schema.py): `users` table

No migration system yet:

- schema is created through `Base.metadata.create_all()`
- no Alembic setup is present

## Backend Routes

Implemented routes:

- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`

Main files:

- [`api/routes/health.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/health.py)
- [`api/routes/auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/auth.py)
- [`api/dependencies/auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/dependencies/auth.py)

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

- [`src/app/login/page.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/app/login/page.tsx)
- [`src/app/dashboard/page.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/app/dashboard/page.tsx)
- [`src/components/dashboard/dashboard-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/dashboard-shell.tsx)
- [`src/components/dashboard/anomalies-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/anomalies-shell.tsx)
- [`src/components/dashboard/department-detail-shell.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/dashboard/department-detail-shell.tsx)

Supporting areas:

- [`src/components/auth`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/auth)
- [`src/components/shared`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/components/shared)
- [`src/lib/api`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/api)
- [`src/lib/mappers.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/mappers.ts)
- [`src/lib/formatters.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/formatters.ts)

## Frontend-Backend Gap

The biggest current seam:

- frontend already has dashboard pages and API client methods
- backend does not yet implement the dashboard data routes those pages call

Frontend-anticipated backend routes not yet implemented:

- `GET /api/summary`
- `GET /api/departments`
- `GET /api/trends`
- `GET /api/claims/breakdown`
- `GET /api/anomalies`
- `GET /api/departments/{id}`
- `GET /api/departments/{id}/employees`
- `GET /api/claims`
- `GET /api/refresh/status`
- `POST /api/refresh`

Primary file for this expectation:

- [`src/lib/api/dashboard.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/api/dashboard.ts)

When an agent is asked to "make dashboard work", verify this seam first.

## Tests Map

Backend tests:

- [`apps/backend/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit): health, hashing, auth service
- [`apps/backend/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration): auth and health endpoints

Frontend tests:

- [`apps/frontend/src/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/unit): cards, login form, mappers, tables, shared components, refresh widgets
- [`apps/frontend/src/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration): login flow, dashboard flow, anomaly navigation, refresh UX

Useful first test files:

- [`apps/backend/tests/unit/test_auth_service.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit/test_auth_service.py)
- [`apps/backend/tests/integration/test_auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration/test_auth.py)
- [`apps/frontend/src/tests/integration/dashboard-flow.test.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration/dashboard-flow.test.tsx)
- [`apps/frontend/src/tests/integration/refresh-ux.test.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration/refresh-ux.test.tsx)

## Progress Snapshot

From [`doc/tasks/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/progress.md):

- done: project bootstrap
- done: auth
- done: frontend dashboard
- not started: api
- not started: source sync
- not started: ontology mapping
- not started: analytics aggregation
- not started: anomaly detection
- not started: insight generation
- not started: refresh orchestration
- not started: reporting and export
- not started: data store
- not started: quality gates and CI

Use this as planning context, not proof. Check the touched task doc if scope questions matter.

## Known Drift Hotspots

Verify these before trusting the snapshot:

- backend route inventory
- frontend API client route list
- task progress checklist
- package versions
- whether placeholder modules have become real modules

## Refresh Rules

Refresh this file when:

- a new route group is added or removed
- a placeholder module becomes implemented
- a major page or shell is added
- shared package usage becomes real
- the task progress doc changes materially

Do not update this file for small internal refactors that do not change navigation.
