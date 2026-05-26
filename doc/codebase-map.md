# Codebase Map

Snapshot doc for agent orientation. Use this to avoid blind repo-wide
searching. If this file conflicts with the code, trust the code and refresh
this file.

## Last Verified

- Date: 2026-05-22
- Verified areas:
  - top-level repo layout
  - backend implemented routes and service areas
  - DB schema and migration presence
  - frontend page structure, API client surface, and canonical component folders
  - task progress snapshot (individual task files removed; progress.md kept)
  - doc folder cleanup and path fixes
- Confidence:
  - high for auth, sync, ontology, analytics, anomalies, exports, refresh, and dashboard shell areas
  - high for v2-v6 extension modules (connection, ingestion, cleaning, multi-tenant, workbench)
  - medium for insight-generation depth without a deeper behavior review
  - high for progress docs

## Read This After

1. [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/Canopy/ARCHITECTURE.md)
2. [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/Canopy/QUICKSTART.md)
3. [`doc/README.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/README.md)

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

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/Canopy/ARCHITECTURE.md): system source of truth
- [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/Canopy/DESIGN.md): visual design source of truth
- [`QUICKSTART.md`](C:/Users/Lih%20Sheng/Documents/Canopy/QUICKSTART.md): setup, run, test, lint
- [`doc/README.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/README.md): docs index
- [`doc/tasks/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/progress.md): task index for the versioned trackers
- [`doc/v2/plan.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/v2/plan.md): v2 planning reference (delivered)

## Current Delivery State

v1-v6 baseline delivered. All modules in production.

v1 (Canopy Intelligence intelligence baseline):
- backend auth, source sync (6 entity readers), ontology mapping (domain types,
  6 mappers), analytics aggregation, anomaly detection, export, refresh, insight
  generation, API routes
- frontend login flow, dashboard shells, cards, tables, charts, refresh widgets

v2 (Dashboard shell and navigation):
- analytics shell with sidebar, tenant switcher, page navigation
- department detail, profile, reports views, API contract upgrades

v3 (Ingestion and cleaning):
- upload wizard, workbook profiling, mapping review grid
- cleaning rule builder, cleaning engine, normalization, lineage graph
- template library, publish review, Excel source adapter

v4 (Workspace and dataset):
- project workspace, source catalog, connection model
- dataset workspace with preview grid and health panel
- run progress, history, v3-to-v4 migration layer

v5 (Multi-tenant platform):
- tenant access context, data routing with RLS
- control plane provisioning, object storage isolation
- quotas, job queues, cache, backup, restore, cloning

v6 (Data connection workbench):
- source catalog (static file + MySQL), raw import capture
- deterministic cleaning pipeline, immutable dataset versioning
- lineage workspace integration, dataset workspace visualization

Still worth checking for product depth, not for module existence:

- insight-generation quality and prompt design
- export workbook breadth versus product expectations
- refresh orchestration production-hardening assumptions
- shared `packages/*`
- `infra/`

Practical summary:

- full stack deployed: FastAPI backend + Next.js frontend
- v1-v6 baseline complete across auth, sync, ontology, analytics, anomaly,
  export, refresh, insight, dashboard shell, ingestion, cleaning, workspace,
  dataset, multi-tenant, and data connection workbench
- insight generation is present and wired, but should still be reviewed for
  product depth when behavior changes
- individual task files removed from doc/tasks/vN; progress.md kept as
  completion record

## Backend Map

Entrypoint:

- [`apps/backend/app.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/app.py): FastAPI app factory, middleware, exception handling, router registration

Implemented backend areas:

- [`apps/backend/common`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/common): config, DB wiring, error classes, clock, logging
- [`apps/backend/auth`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/auth): domain, repository, password hashing, JWT/session service, ORM user model
- [`apps/backend/api`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api): health/auth/dashboard/departments/claims/anomalies/exports/refresh routes, request/response schemas, auth dependency
- [`apps/backend/ingestion`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/ingestion): workbook profiling, cleaning, normalization, lineage, templates, publish, source adapters
- [`apps/backend/project`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/project): project workspace domain, repository, service
- [`apps/backend/source_type`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/source_type): source catalog domain, repository, service
- [`apps/backend/connection`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/connection): connection setup, preview, materialization, repository, service
- [`apps/backend/dataset`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/dataset): dataset domain, preview, repository, service
- [`apps/backend/run`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/run): run domain, repository, service
- [`apps/backend/analytics`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/analytics): aggregate reads, rankings, deltas, departments, repositories
- [`apps/backend/anomalies`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/anomalies): anomaly rules, repository, list/detail mapping
- [`apps/backend/insights`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/insights): domain, service, generation entrypoints
- [`apps/backend/exports`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/exports): workbook build and export payload composition
- [`apps/backend/refresh`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/refresh): trigger, status, job reads, orchestration entrypoints
- [`apps/backend/control_plane`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/control_plane): tenant admin, provisioning, lifecycle, audit, config, membership, tenant repository
- [`apps/backend/tenant_data`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/tenant_data): tenant storage base, RLS, migration pipeline, router, schema bundles
- [`apps/backend/object_storage`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/object_storage): object storage access guard, adapter layer, key generation, service
- [`apps/backend/backup`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/backup): backup, restore, clone, policy, lifecycle validation
- [`apps/backend/cache`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/cache): cache store, config cache, invalidation hooks, routing cache
- [`apps/backend/quotas`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/quotas): quota registry, evaluator, enforcer, usage tracking
- [`apps/backend/job_queue`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/job_queue): job registry and tenant queue scheduling

Current DB models:

- [`apps/backend/auth/schema.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/auth/schema.py): `users`
- [`apps/backend/sync/schema.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/sync/schema.py): source snapshot tables
- [`apps/backend/ontology/schema.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/ontology/schema.py): ontology and unresolved mapping tables
- [`apps/backend/control_plane/schemas`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/control_plane/schemas): tenant admin, audit, config, membership, and provisioning tables
- [`apps/backend/tenant_data/schemas`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/tenant_data/schemas): tenant data plane tables and schema bundles
- analytics, anomalies, refresh, and related modules have supporting persistence and repositories in their own areas

Source-side models (separate read-only base):

- [`apps/backend/sync/readers/_source_models.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/sync/readers/_source_models.py): `departments`, `employees`, `claims`, `payroll`, `cost_centers`, `budget_codes`

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

- [`apps/backend/api/routes/health.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/health.py)
- [`apps/backend/api/routes/auth.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/auth.py)
- [`apps/backend/api/routes/dashboard.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/dashboard.py)
- [`apps/backend/api/routes/departments.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/departments.py)
- [`apps/backend/api/routes/claims.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/claims.py)
- [`apps/backend/api/routes/anomalies.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/anomalies.py)
- [`apps/backend/api/routes/exports.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/exports.py)
- [`apps/backend/api/routes/refresh.py`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/api/routes/refresh.py)

## Frontend Map

Frontend app root:

- [`apps/frontend/src/app`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/app)

Main routes:

- `/` -> redirects to `/dashboard`
- `/login`
- `/dashboard`
- `/dashboard/anomalies`
- `/dashboard/departments/[id]`

First places to inspect:

- [`apps/frontend/src/app/login/page.tsx`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/app/login/page.tsx)
- [`apps/frontend/src/app/dashboard/page.tsx`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/app/dashboard/page.tsx)
- [`apps/frontend/src/components/dashboard/dashboard-shell.tsx`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/components/dashboard/dashboard-shell.tsx)
- [`apps/frontend/src/components/dashboard/anomalies-shell.tsx`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/components/dashboard/anomalies-shell.tsx)
- [`apps/frontend/src/components/dashboard/department-detail-shell.tsx`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/components/dashboard/department-detail-shell.tsx)

Supporting areas:

- [`apps/frontend/src/components/auth`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/components/auth)
- [`apps/frontend/src/components/shared`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/components/shared)
- [`apps/frontend/src/lib/api`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/lib/api)
- [`apps/frontend/src/lib/mappers.ts`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/lib/mappers.ts)
- [`apps/frontend/src/lib/formatters.ts`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/lib/formatters.ts)

## Frontend-Backend Shape

Main current seam to verify before deeper work:

- whether current dashboard, anomaly, export, refresh, and insight behavior is product-complete enough for v2 goals
- whether the code matches the completed task checklists at product depth, not only module existence

## Tests Map

Backend tests:

- [`apps/backend/tests/unit`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/tests/unit)
- [`apps/backend/tests/integration`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/backend/tests/integration)

Frontend tests:

- [`apps/frontend/src/tests/unit`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/tests/unit)
- [`apps/frontend/src/tests/integration`](C:/Users/Lih%20Sheng/Documents/Canopy/apps/frontend/src/tests/integration)

## Progress Snapshot

All v1-v6 task modules delivered. Individual task files removed; progress.md
files kept as completion records.

Versioned progress trackers:

- [`doc/tasks/v1/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v1/progress.md): v1 baseline — 13/13 complete
- [`doc/tasks/v2/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v2/progress.md): v2 dashboard shell — 10/11 complete (tenant-switching pending)
- [`doc/tasks/v3/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v3/progress.md): v3 ingestion and cleaning — 11/11 complete
- [`doc/tasks/v4/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v4/progress.md): v4 workspace and dataset — 10/10 complete
- [`doc/tasks/v5/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v5/progress.md): v5 multi-tenant platform — 6/6 complete
- [`doc/tasks/v6/progress.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/tasks/v6/progress.md): v6 data connection workbench — 10/10 complete

## Known Drift Hotspots

Verify these before trusting the snapshot:

- route inventory under `apps/backend/api/routes/`
- frontend API client expectations under `apps/frontend/src/lib/api/`
- whether current v2-v6 code matches the progress.md completion records
- package versions

## Refresh Rules

Refresh this file when:

- a new route group is added or removed
- a major module changes status materially
- a new version phase delivers and its progress.md records completion
- the task progress docs change materially

Do not update this file for small internal refactors that do not change
navigation or module status.
