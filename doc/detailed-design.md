# Detailed Design: Executive HR Spend Intelligence Platform

> Historical note:
> This document is the detailed v1 design baseline. V1 is now complete.
> Keep it as the implementation design record for v1 and the baseline reference
> for v2 planning. Do not treat the sequencing sections below as the current
> active delivery plan.

## Purpose

This document captured the implementation-ready design for v1. It defines the
intended module internals, key data structures, control flow, public
interfaces, persistence boundaries, error handling, and test strategy that
shaped the completed v1 system.

This document follows:

- `doc/proposal.md`
- `doc/high-level-design.md`
- `ARCHITECTURE.md`
- `DESIGN.md`

If any of those documents conflict, `ARCHITECTURE.md` is the source of truth
for system architecture and `DESIGN.md` is the source of truth for visual UI
behavior.

---

## Implementation goals

V1 was designed to let an authenticated executive:

- view monthly payroll and claim spend summaries
- identify departments with unusual month-over-month changes
- drill into department, employee, claim type, and month detail
- read grounded AI-generated insight summaries
- trigger manual refresh
- export dashboard-aligned Excel output

V1 was designed to remain:

- read-only against the source system
- deterministic in analytics and anomaly logic
- consistent across dashboard, export, and AI summary snapshot usage

---

## Concrete module layout

The codebase should be structured as a modular monolith with one frontend app,
one backend app, and clearly separated backend domains.

Recommended top-level shape:

```text
apps/
  frontend/                  Next.js application
  backend/                   FastAPI application

packages/
  domain/                    ontology models and shared business types
  analytics/                 aggregation and anomaly logic
  sync/                      source readers and normalization pipeline
  insights/                  AI summary input builders and output handlers
  exports/                   Excel export builders
  shared/                    shared config, helpers, and cross-app contracts

infra/
  jobs/                      worker and scheduler setup
  scripts/                   local dev and operational scripts
```

If the repo later stays smaller than this, the same boundaries may live as
folders inside `apps/backend` rather than as separate packages. The boundary is
mandatory even if the physical packaging stays simpler.

## Modularization rules

The implementation should optimize for small, testable units.

Required rules:

- module boundaries follow responsibility, not framework layer convenience
- business logic must be callable without HTTP request objects
- data shaping must be callable without rendering a page
- persistence must be replaceable with test doubles in service tests
- each module exposes a narrow public surface and keeps helpers private

Preferred test seam order:

1. pure functions
2. service/use-case modules with mocked dependencies
3. repository and gateway adapters
4. route/page integration
5. end-to-end smoke

If a feature can only be tested through a full-stack flow, the module split is
too coarse and should be refined.

## Required dependency direction

Allowed direction:

- frontend pages -> frontend hooks/adapters -> backend APIs
- backend routes -> use-case services -> repositories/gateways
- sync readers -> mappers -> ontology persistence
- analytics aggregators -> anomaly rules -> insight builders

Forbidden direction:

- pages importing backend contract internals directly
- components calling fetch inline
- route handlers doing aggregation or anomaly math inline
- repositories coordinating business workflows
- anomaly rules depending on ORM models or framework request objects
- insight builders querying source data directly

---

## Frontend design

## Main frontend responsibilities

The frontend is responsible for:

- login screen and session lifecycle handling
- dashboard composition from backend-provided read models
- loading, empty, stale, and error states
- drill-down navigation and filter state
- manual refresh initiation and status display
- export initiation

The frontend is not responsible for:

- computing anomaly logic
- deriving executive metrics from raw records
- merging payroll and claims business rules
- generating AI recommendations locally

## Frontend route map

Recommended v1 pages:

- `/login`
- `/dashboard`
- `/dashboard/departments/[department_id]`
- `/dashboard/employees/[employee_id]`
- `/dashboard/anomalies`
- `/dashboard/refresh`

If the product prefers modal or panel drill-down instead of dedicated pages,
the backend contract remains the same. Route design can stay page-based first
for simpler implementation and testing.

## Frontend component groups

Recommended component groups:

- `auth/`
  - login form
  - session guard
- `dashboard/summary/`
  - total payroll card
  - total claims card
  - top departments card
  - anomaly highlights card
- `dashboard/charts/`
  - monthly trend chart
  - department ranking chart
  - claim type breakdown chart
- `dashboard/drilldown/`
  - department detail header
  - employee contribution table
  - claim detail table
  - period filter controls
- `dashboard/refresh/`
  - refresh status badge
  - refresh timeline panel
  - manual refresh button
- `shared/`
  - page shell
  - loading states
  - empty states
  - error panels

Implementation rule:

- separate container components from presentational components
- containers own data loading and action wiring
- presentational components receive plain typed props
- chart-specific mappers live beside charts, not inside page files

## Frontend state model

Frontend state should be split into:

- server state
  - dashboard summaries
  - trend data
  - anomaly list
  - drill-down datasets
  - refresh job status
- UI state
  - selected filters
  - expanded cards
  - active drill-down target
  - export intent state

Recommended approach:

- use typed API client functions
- use React Query for server state fetching and cache invalidation
- keep route state and filter state serializable

State splitting rule:

- one hook owns one server resource family
- one hook should not silently merge unrelated backend resources unless that is
  the explicit use case
- derived display data should live in mapper functions, not hidden inside JSX

## Frontend API adapter boundary

Frontend code must not consume raw backend JSON directly inside components.

Use an adapter layer:

- `api/client.ts`
- `api/summary.ts`
- `api/departments.ts`
- `api/anomalies.ts`
- `api/refresh.ts`
- `api/exports.ts`

Each adapter:

- calls one backend route
- validates the response shape at the boundary
- maps server DTOs into UI-facing types where needed

Adapter rule:

- adapters do transport and mapping only
- no UI formatting
- no chart-specific decisions
- no local fallback business rules that can diverge from backend truth

## Frontend design-system boundary

`DESIGN.md` defines the UI language. Detailed implementation should enforce:

- shared tokens file for spacing, color, type, and surface mappings
- no ad hoc component-local styling drift for dashboard primitives
- reusable card, table, panel, badge, and chart wrappers
- distinct stale/loading/error visual states

Implementation note:

- build one shared dashboard card frame and compose metric-specific content
- build one shared drill-down table shell and swap column definitions

---

## Backend design

## Backend module map

Recommended backend internal structure:

```text
apps/backend/
  api/
    routes/
    schemas/
    dependencies/
  auth/
    service.py
    repository.py
    hashing.py
    tokens.py
  sync/
    readers/
    mappers/
    orchestration/
    repositories/
  ontology/
    models/
    repositories/
  analytics/
    aggregators/
    queries/
    services/
  anomalies/
    rules/
    service.py
  insights/
    prompt_builder.py
    service.py
    fallback.py
  exports/
    workbook_builder.py
    service.py
  refresh/
    jobs/
    service.py
    repository.py
  common/
    config.py
    logging.py
    errors.py
    clock.py
```

Recommended sub-splitting for testability:

- `analytics/aggregators/`
  - `payroll_monthly.py`
  - `claims_monthly.py`
  - `department_totals.py`
- `anomalies/rules/`
  - `department_total_spike.py`
  - `department_claim_spike.py`
  - `historical_outlier.py`
- `insights/`
  - `input_builder.py`
  - `llm_client.py`
  - `fallback_summary.py`
- `refresh/jobs/`
  - `extract_source.py`
  - `normalize_ontology.py`
  - `rebuild_aggregates.py`
  - `detect_anomalies.py`
  - `generate_insights.py`
  - `publish_snapshot.py`

## Backend architectural rules

- route handlers stay thin
- repositories handle persistence access
- services coordinate business use cases
- pure business rules stay in isolated functions where possible
- source readers are separate from ontology repositories
- AI integration is downstream of analytics and anomaly generation
- services depend on interfaces or narrow repository/gateway contracts
- no module should need the whole application container just to test one rule
- each refresh stage should be executable and testable independently

## Key use-case services

Recommended service entry points:

- `AuthService`
  - login
  - logout
  - validate_session
- `DashboardSummaryService`
  - get executive summary
  - get finance trend view
  - get workforce trend view
- `DepartmentAnalysisService`
  - get department detail
  - get department monthly trend
  - get department contributors
- `AnomalyService`
  - compute anomalies for snapshot
  - fetch anomaly views
- `RefreshService`
  - request manual refresh
  - get current refresh status
  - finalize successful snapshot
- `SyncService`
  - extract source data
  - persist source snapshot
  - trigger normalization
- `OntologyMappingService`
  - map source rows into ontology rows
- `AggregationService`
  - rebuild monthly aggregates
- `InsightService`
  - build summary inputs
  - generate summary text
  - store fallback summary on LLM failure
- `ExportService`
  - build workbook from snapshot-aligned read models

Use-case service rule:

- a service should own one business workflow
- if a service grows to many unrelated methods, split it before implementation
- orchestration services may call multiple narrow services, but narrow services
  should not depend on orchestration services

---

## Data model design

## Logical data zones

The database should be organized into these logical groups:

- auth and application metadata
- source snapshot/staging
- ontology
- analytics
- anomaly cache
- insight cache
- refresh and job tracking

## Core entity model

### Application metadata

- `users`
  - id
  - email
  - password_hash
  - display_name
  - created_at
  - last_login_at
  - is_active

- `refresh_jobs`
  - id
  - trigger_type
  - status
  - requested_by_user_id
  - started_at
  - finished_at
  - error_message
  - produced_snapshot_id

- `data_snapshots`
  - id
  - source_extracted_at
  - normalized_at
  - aggregated_at
  - anomalies_generated_at
  - insights_generated_at
  - status
  - is_current

### Source snapshot zone

Store raw or near-raw source extracts for traceability.

Recommended tables:

- `source_departments_snapshot`
- `source_employees_snapshot`
- `source_claims_snapshot`
- `source_payroll_snapshot`
- `source_cost_centers_snapshot`
- `source_budget_codes_snapshot`

Minimum shared columns:

- id
- snapshot_id
- source_record_key
- source_payload_json
- extracted_at

If the source volume is large, store compact normalized staging columns plus
the raw payload only where audit value is high.

### Ontology zone

- `departments`
  - id
  - snapshot_id
  - source_department_key
  - name
  - parent_department_id
  - status

- `employees`
  - id
  - snapshot_id
  - source_employee_key
  - department_id
  - cost_center_id
  - employee_code
  - full_name
  - employment_status

- `cost_centers`
  - id
  - snapshot_id
  - source_cost_center_key
  - code
  - name

- `budget_codes`
  - id
  - snapshot_id
  - source_budget_code_key
  - code
  - name
  - category

- `expense_claims`
  - id
  - snapshot_id
  - source_claim_key
  - employee_id
  - department_id
  - cost_center_id
  - budget_code_id
  - claim_type
  - claim_date
  - amount
  - currency

- `payroll_expenses`
  - id
  - snapshot_id
  - source_payroll_key
  - employee_id
  - department_id
  - cost_center_id
  - budget_code_id
  - payroll_month
  - amount
  - currency
  - pay_component

## Analytics zone

Recommended derived tables:

- `monthly_department_spend`
  - snapshot_id
  - month_key
  - department_id
  - payroll_amount
  - claims_amount
  - total_amount

- `monthly_employee_spend`
  - snapshot_id
  - month_key
  - employee_id
  - department_id
  - payroll_amount
  - claims_amount
  - total_amount

- `monthly_claim_type_spend`
  - snapshot_id
  - month_key
  - department_id
  - claim_type
  - amount

- `dashboard_summary_cache`
  - snapshot_id
  - summary_key
  - summary_payload_json

## Anomaly zone

- `detected_anomalies`
  - id
  - snapshot_id
  - anomaly_type
  - target_entity_type
  - target_entity_id
  - month_key
  - baseline_value
  - observed_value
  - delta_value
  - delta_percent
  - driver_payload_json
  - severity

## Insight cache zone

- `generated_insights`
  - id
  - snapshot_id
  - insight_scope
  - target_entity_id
  - input_facts_json
  - output_text
  - generation_status
  - fallback_used
  - generated_at

---

## Data mapping rules

## Mapping principles

- source schema knowledge is isolated to sync readers and mappers
- ontology rows are snapshot-scoped
- payroll and claims remain distinct entities
- mapping preserves source lineage
- money values use fixed decimal types, never float
- each mapper should map one source entity family only
- cross-entity resolution should happen in orchestration or dedicated resolver
  modules, not inside unrelated mappers

## Employee identity resolution

Employee identity may come from several source structures. The mapper should:

- define one canonical employee key per snapshot
- merge required HR identity fields into one employee row
- preserve the original source keys for traceability

## Department attribution rules

Claim and payroll rows should be attributed using the best available data in
this order:

1. direct department on the source record
2. employee-linked department at snapshot time
3. mapped fallback from cost center if a trustworthy mapping exists

If attribution is impossible:

- keep the row in staging
- flag the mapping issue
- exclude it from executive aggregates until resolved

Do not silently assign unknown spend to a fake department bucket unless the
product explicitly decides to surface such a bucket.

---

## Analytics and anomaly design

## Aggregation pipeline

For each completed snapshot:

1. aggregate payroll totals by month, department, employee, and cost center
2. aggregate claim totals by month, department, employee, claim type, and cost
   center
3. merge payroll and claims into dashboard-ready monthly spend views
4. compute rankings and month-over-month deltas
5. persist dashboard summary cache records

Aggregation modularity rule:

- compute payroll and claims aggregates separately first
- merge at the read-model layer after independent validation
- ranking, delta, and contribution logic should be separate functions so tests
  can isolate failures quickly

## Monthly period rules

- monthly views are the primary grain for v1
- dashboard trend range should support 6 to 12 months
- payroll uses payroll month
- claims use claim transaction month
- mixed-source totals align by calendar month key

## Anomaly rule set

V1 anomaly rules should begin with deterministic, explainable rules.

Recommended initial rules:

- month-over-month department total spend spike
- month-over-month department claim spend spike
- top-department unusual increase compared with recent historical average

Each anomaly rule should output:

- anomaly type
- target department
- target month
- baseline value
- observed value
- delta amount
- delta percent
- likely drivers
- drill-down keys

## Anomaly severity

Severity should be application-defined, not model-defined.

Recommended first pass:

- `low`
- `medium`
- `high`

Severity can be based on:

- absolute delta thresholds
- percentage delta thresholds
- contribution concentration from a few employees or claim types

Exact thresholds should be kept in config, not hardcoded inside route handlers.

Rule packaging requirement:

- each anomaly rule file exports one evaluation function
- one coordinator combines rule outputs for a snapshot
- severity classification should be split from anomaly detection when practical

---

## Insight generation design

## Input contract for AI generation

The LLM input must be structured and bounded. It should include:

- snapshot metadata
- current month totals
- previous month totals
- top departments by spend
- anomaly list with computed facts
- major contributing claim types
- major contributing employees or clusters where supported

It must not include:

- raw unbounded operational rows
- open-ended prompts with no fact structure
- credentials or secrets

## Output contract for AI generation

The stored summary output should include:

- headline summary
- key changes
- likely drivers
- recommended review areas
- provenance metadata

Required metadata:

- snapshot_id
- generated_at
- model_identifier
- fallback_used

## Fallback behavior

If AI generation fails:

- log the failure reason
- produce a deterministic summary from the same structured facts
- mark `fallback_used = true`
- keep the dashboard usable

Insight modularity rule:

- fact extraction, prompt building, LLM invocation, response parsing, and
  fallback summary generation should be separate units
- tests must be able to validate each unit without performing a real model call

---

## Refresh orchestration design

## Refresh job states

Recommended job statuses:

- `queued`
- `running`
- `failed`
- `completed`

Recommended pipeline stages:

- `extract_source`
- `persist_snapshot`
- `normalize_ontology`
- `rebuild_aggregates`
- `detect_anomalies`
- `generate_insights`
- `publish_snapshot`

## Refresh control flow

Manual refresh request flow:

1. authenticated user clicks refresh
2. API validates no conflicting refresh policy violation
3. API creates `refresh_jobs` row with `queued`
4. worker claims job and marks `running`
5. worker executes stages in order
6. on success, worker marks produced snapshot as current
7. on failure, worker preserves last known-good snapshot and records failure

Refresh modularity rule:

- each pipeline stage should be implemented as an isolated command/use-case
- stage outputs should be explicit and persisted, not hidden in in-memory
  globals
- publish step must be a separate final action, never an incidental side effect

## Publish rules

A snapshot becomes current only when:

- extraction succeeded
- normalization succeeded
- aggregates succeeded
- anomaly computation succeeded
- insight generation succeeded or deterministic fallback succeeded

This prevents partial refresh state from becoming user-visible truth.

---

## API contract design

## Response envelope

Use one consistent response shape:

```ts
type ApiResponse<T> = {
  success: boolean
  data: T | null
  error: string | null
  meta?: {
    snapshotId?: string
    snapshotDate?: string
    generatedAt?: string
  }
}
```

## Route groups

### Auth

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`

### Dashboard summary

- `GET /api/dashboard/summary`
- `GET /api/dashboard/trends`
- `GET /api/dashboard/top-departments`

### Departments and drill-down

- `GET /api/departments`
- `GET /api/departments/{department_id}`
- `GET /api/departments/{department_id}/trends`
- `GET /api/departments/{department_id}/employees`
- `GET /api/departments/{department_id}/claim-types`

### Anomalies

- `GET /api/anomalies`
- `GET /api/anomalies/{anomaly_id}`

### Refresh

- `POST /api/refresh`
- `GET /api/refresh/current`
- `GET /api/refresh/jobs/{job_id}`

### Exports

- `POST /api/exports/executive-summary`

## API schema rules

- all request and response payloads use explicit schema models
- no anonymous dict payloads passed through services
- dates and month keys use normalized formats
- money values use decimal-safe serialization

API modularity rule:

- schemas define transport contracts only
- route handlers translate between transport schemas and service DTOs
- service DTOs should remain stable even if HTTP contract later changes

---

## Error handling design

## Error categories

Recommended application error classes:

- authentication error
- authorization error
- validation error
- source sync error
- mapping error
- aggregation error
- anomaly generation error
- insight generation error
- export generation error

## Error behavior rules

- validation errors return client-safe messages
- internal processing failures return stable generic API errors
- refresh job failures are visible through refresh status endpoints
- partial refresh failure never removes last known-good dashboard data

## User-visible state rules

Frontend must distinguish:

- loading
- empty result
- stale but usable
- failed refresh
- fatal data load failure

The user should always know whether they are viewing current data or the last
successful snapshot.

---

## Security design

## Authentication

V1 uses simple email/password authentication.

Implementation requirements:

- password hashing with a standard secure algorithm
- session or token validation at backend boundary
- protected dashboard and refresh routes

## Source protection

- source credentials are server-side only
- frontend never sees source connection details
- source reads are isolated to sync code

## AI safety boundary

- AI receives structured business facts only
- no write-path capability
- no execution of recommendations

---

## Testing strategy

Testing is required for both frontend and backend from the start.

## Frontend unit testing

Recommended tool direction:

- test runner for TypeScript and React component tests
- React Testing Library style component tests

Must cover:

- summary cards render expected metric values
- anomaly cards render severity and driver summaries correctly
- trend components handle series gaps, empty states, and loading states
- drill-down tables render mapped rows correctly
- refresh widgets handle queued, running, failed, and completed states
- API adapter mappers convert backend payloads into UI types correctly

Unit-test target areas:

- presentational components
- hooks with mocked API responses
- formatters and derived UI mappers
- route guards and session helpers

Preferred frontend test shape:

- component tests pass plain props
- hook tests mock adapter boundaries, not low-level fetch globally
- mapper tests use table-driven fixtures
- page tests verify composition and navigation, not every visual branch

## Frontend integration testing

Must cover:

- login to dashboard happy path with mocked backend
- dashboard to department drill-down flow
- anomaly list to anomaly detail flow
- manual refresh trigger and status polling flow
- export initiation flow

## Backend unit testing

Recommended tool direction:

- Python unit test framework
- isolated tests for pure functions and service helpers

Must cover:

- source-to-ontology mapper functions
- monthly aggregation logic
- anomaly rule functions
- severity classification logic
- AI input payload builder
- deterministic fallback summary builder
- auth validation helpers

Highest-confidence unit-test targets:

- aggregation formulas
- anomaly detection rules
- snapshot publication rules
- payroll/claims merge logic

Preferred backend test shape:

- mapper tests with source fixture rows and exact normalized output
- aggregator tests with small snapshot fixtures and exact totals
- anomaly tests one rule at a time with explicit threshold scenarios
- service tests with mocked repositories, LLM client, and clock

## Backend integration testing

Must cover:

- auth endpoints
- dashboard summary endpoints
- department drill-down endpoints
- anomaly endpoints
- refresh job creation and status endpoints
- export endpoint
- snapshot publication behavior after successful refresh
- failure path preserving last known-good snapshot

## End-to-end smoke scope

One lightweight smoke path should prove:

1. login works
2. dashboard renders summary data
3. drill-down works
4. refresh request can be created
5. export request succeeds

## Coverage and CI expectations

Recommended CI gates:

- frontend lint
- frontend typecheck
- frontend unit tests
- frontend integration tests
- backend lint/format validation
- backend unit tests
- backend integration tests

Recommended stricter rules:

- anomaly and aggregation modules carry the strongest coverage threshold
- no merge allowed when core business-rule tests fail
- no merge allowed when API schema tests fail
- no merge allowed when a module becomes effectively untestable without
  full-stack boot for ordinary business rules

Exact percentages can be decided later, but the architecture requires:

- high confidence in analytics logic
- high confidence in snapshot consistency logic
- regression coverage for dashboard contracts

---

## Delivery sequencing

Historical note:
This was the recommended v1 build order before implementation. It is preserved
for auditability, not as the active roadmap.

Original recommended build order:

1. backend schema and snapshot model
2. source sync skeleton and raw snapshot persistence
3. ontology mapping
4. monthly aggregation
5. anomaly detection
6. dashboard read APIs
7. frontend dashboard shell
8. drill-down pages
9. refresh flow
10. insight generation
11. export flow
12. CI hardening and expanded integration coverage

This order keeps deterministic data logic ahead of AI and presentation polish.

---

## Main implementation risks

- source schema ambiguity may complicate employee and department attribution
- payroll data may not support clean employee-level drill-down in all cases
- cost center coverage may be incomplete
- month-over-month anomaly thresholds may need tuning after real data exposure
- refresh jobs may become slow if snapshot persistence and aggregation are not
  indexed properly
- AI summaries may sound plausible even when low value, so deterministic fact
  structure and fallback are critical

---

## Decisions locked by this document

- v1 stays modular monolith, not microservices
- frontend uses Next.js and TypeScript
- backend uses FastAPI and Python
- internal database is read-only source input
- payroll and claims remain separate ontology families
- analytics and anomalies are deterministic application logic
- AI is a summary layer only
- manual refresh is asynchronous
- dashboard, export, and AI share the same published snapshot basis
- FE and BE tests are mandatory, not optional later work
