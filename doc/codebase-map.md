# Codebase Map

Snapshot doc for agent orientation. Use this to avoid blind repo-wide searching.
If this file conflicts with the code, trust the code and refresh this file.

## Last Verified

- Date: 2026-05-15
- Verified areas:
  - top-level repo layout
  - backend implemented routes, auth, sync, and ontology modules
  - DB schema inventory
  - frontend page structure and API client surface
  - task progress snapshot
- Confidence:
  - high for auth, sync, ontology, and dashboard shell areas
  - medium for placeholder analytics/anomaly/insight/export/refresh modules
  - medium for progress docs (verified task docs, trusting them)

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

Implemented and tested:

- backend auth flow (login, logout, session, JWT)
- backend health endpoint
- backend source sync (6 entity readers, snapshot persistence, orchestration)
- backend ontology mapping (domain types, 6 mappers, attribution resolver, persistence, orchestrator)
- backend API route groups (dashboard, departments, claims, anomalies, exports, refresh) with placeholder service stubs
- frontend login flow
- frontend dashboard UI shells, cards, tables, charts, and refresh widgets
- frontend tests for auth/dashboard components and flows
- backend tests for auth, health, sync, ontology (126 total)

Mostly placeholders:

- analytics aggregation (hardcoded sample data stubs in `analytics/service.py` and `analytics/departments.py`)
- anomaly detection backend (hardcoded sample data stubs in `anomalies/service.py`)
- insight generation backend (`insights/__init__.py` empty)
- export backend (`exports/service.py` returns "queued" stub)
- refresh orchestration backend (`refresh/service.py` stub)
- shared `packages/*`
- `infra/`

Practical summary:

- backend has real auth, sync, and ontology modules
- analytics, anomalies, insights, exports, and refresh are stubs returning hardcoded data
- frontend is ahead of backend and already expects real dashboard APIs

## Backend Map

Entrypoint:

- [`apps/backend/app.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/app.py): FastAPI app factory, middleware, exception handling, router registration

Implemented backend areas:

- [`apps/backend/common`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/common): config, DB wiring, error classes, clock, logging
- [`apps/backend/auth`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth): domain, repository, password hashing, JWT/session service, ORM user model
- [`apps/backend/api`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api): health/auth/dashboard/departments/claims/anomalies/exports/refresh routes, request/response schemas, auth dependency
- [`apps/backend/sync`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync): 6 source readers, snapshot repository, sync orchestrator, source DB wiring
- [`apps/backend/ontology`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology): domain types, 6 mappers (department, employee, cost center, budget code, claim, payroll), attribution resolver, ontology repository, orchestrator

Stub/placeholder backend areas (return hardcoded data):

- [`apps/backend/analytics`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/analytics): hardcoded dashboard summary, trends, departments
- [`apps/backend/anomalies`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/anomalies): hardcoded anomaly list/detail
- [`apps/backend/insights`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/insights): empty
- [`apps/backend/exports`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/exports): returns "queued"
- [`apps/backend/refresh`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/refresh): stub trigger/status/job

Current DB models (all using `Base` from `common/database.py`):

- [`apps/backend/auth/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/auth/schema.py): `users`
- [`apps/backend/sync/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/schema.py): `source_snapshots`, `source_snapshot_rows`
- [`apps/backend/ontology/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/schema.py): `departments`, `employees`, `cost_centers`, `budget_codes`, `expense_claims`, `payroll_expenses`, `unresolved_mapping_issues`

Source-side models (separate `SourceBase`, read-only):

- [`apps/backend/sync/readers/_source_models.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/readers/_source_models.py): `departments`, `employees`, `claims`, `payroll`, `cost_centers`, `budget_codes`

No migration system yet:

- schema is created through `Base.metadata.create_all()`
- `init_db()` imports `auth.schema`, `sync.schema`, and `ontology.schema`
- no Alembic setup is present

Migration system (Data Store):

- Alembic is installed and configured in `apps/backend/alembic/`
- initial migration at `alembic/versions/a9eb23d92c20_initial_schema.py`
- run with `alembic upgrade head`
- ORM models use `Numeric(precision=12, scale=2, asdecimal=False)` for money columns
- timestamp fields use `DateTime(timezone=True)` with default `datetime.now(UTC)`

## Backend Routes

Implemented routes:

- `GET /api/health`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`

Routes wired with stub services (return hardcoded data):

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

- [`api/routes/health.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/health.py)
- [`api/routes/auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/auth.py)
- [`api/routes/dashboard.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/dashboard.py)
- [`api/routes/departments.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/departments.py)
- [`api/routes/claims.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/claims.py)
- [`api/routes/anomalies.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/anomalies.py)
- [`api/routes/exports.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/exports.py)
- [`api/routes/refresh.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/routes/refresh.py)
- [`api/dependencies/auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/api/dependencies/auth.py)

## Sync Module

Source sync reads from the internal database and persists snapshots. See [`sync/`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/).

- [`sync/domain.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/domain.py): `SourceReader` ABC, 6 source dataclasses, `EntitySnapshot`, `SyncResult`
- [`sync/readers/_source_models.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/readers/_source_models.py): separate `SourceBase` ORM with 6 source tables
- [`sync/readers/`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/readers/): one reader per entity (departments, employees, claims, payroll, cost_centers, budget_codes)
- [`sync/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/schema.py): `source_snapshots`, `source_snapshot_rows` tables
- [`sync/repositories/snapshot.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/repositories/snapshot.py): `SnapshotRepository`
- [`sync/orchestration/service.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/orchestration/service.py): `SyncOrchestrator`
- [`sync/source_db.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/sync/source_db.py): source DB engine/session factory

## Ontology Mapping Module

Converts raw source rows into normalized business objects with source lineage. See [`ontology/`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/).

- [`ontology/domain.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/domain.py): `OntologyMapper` ABC, 6 ontology dataclasses (`Department`, `Employee`, `CostCenter`, `BudgetCode`, `ExpenseClaim`, `PayrollExpense`), `MappingResult`, `UnresolvedRecord`, `MappingContext`
- [`ontology/schema.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/schema.py): 7 ORM models including `unresolved_mapping_issues`
- [`ontology/mappers/departments.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/mappers/departments.py): `DepartmentMapper`, `EmployeeMapper`, `CostCenterMapper`, `BudgetCodeMapper`
- [`ontology/mappers/claims.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/mappers/claims.py): `ClaimMapper` with attribution
- [`ontology/mappers/payroll.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/mappers/payroll.py): `PayrollMapper` with attribution
- [`ontology/mappers/attribution.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/mappers/attribution.py): `AttributionResolver` (direct -> employee-linked -> cost center fallback)
- [`ontology/repositories/ontology.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/repositories/ontology.py): `OntologyRepository`
- [`ontology/orchestration/service.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/ontology/orchestration/service.py): `OntologyOrchestrator` (runs mappers in dependency order)

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
- backend dashboard/department/anomaly routes return hardcoded stub data
- sync and ontology modules are real but not yet plumbed into the API routes

Frontend-anticipated backend routes:

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

Primary file for this expectation:

- [`src/lib/api/dashboard.ts`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/lib/api/dashboard.ts)

When an agent is asked to "make dashboard work", replace the stub services with real implementations backed by sync + ontology data.

## Tests Map

Backend tests (126 total):

- [`apps/backend/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit): health, hashing, auth service, API schemas, sync orchestration, sync readers, ontology mappers, ontology attribution
- [`apps/backend/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration): health, auth, dashboard API, departments API, anomalies API, error envelope, exports API, refresh API, sync snapshot, ontology persistence

Frontend tests:

- [`apps/frontend/src/tests/unit`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/unit): cards, login form, mappers, tables, shared components, refresh widgets
- [`apps/frontend/src/tests/integration`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration): login flow, dashboard flow, anomaly navigation, refresh UX

Useful first test files:

- [`apps/backend/tests/unit/test_auth_service.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit/test_auth_service.py)
- [`apps/backend/tests/unit/test_sync_readers.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit/test_sync_readers.py)
- [`apps/backend/tests/unit/test_ontology_mappers.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit/test_ontology_mappers.py)
- [`apps/backend/tests/unit/test_ontology_attribution.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/unit/test_ontology_attribution.py)
- [`apps/backend/tests/integration/test_auth.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration/test_auth.py)
- [`apps/backend/tests/integration/test_ontology_persistence.py`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/backend/tests/integration/test_ontology_persistence.py)
- [`apps/frontend/src/tests/integration/dashboard-flow.test.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration/dashboard-flow.test.tsx)
- [`apps/frontend/src/tests/integration/refresh-ux.test.tsx`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/apps/frontend/src/tests/integration/refresh-ux.test.tsx)

## Progress Snapshot

From [`doc/tasks/progress.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/tasks/progress.md):

- done: project bootstrap
- done: auth
- done: frontend dashboard
- done: api
- done: source sync
- done: ontology mapping
- not started: analytics aggregation
- not started: anomaly detection
- not started: insight generation
- not started: refresh orchestration
- not started: reporting and export
- done: data store
- not started: quality gates and CI

Use this as planning context, not proof. Check the touched task doc if scope questions matter.

## Known Drift Hotspots

Verify these before trusting the snapshot:

- backend route inventory (check all routes in `api/routes/` still match this map)
- frontend API client route list (check `src/lib/api/dashboard.ts` and siblings)
- task progress checklist (check `doc/tasks/progress.md`)
- package versions
- whether analytics/anomaly/insight/export/refresh placeholders have become real modules

## Refresh Rules

Refresh this file when:

- a new route group is added or removed
- a placeholder module becomes implemented
- a major page or shell is added
- shared package usage becomes real
- the task progress doc changes materially

Do not update this file for small internal refactors that do not change navigation.
