# Canopy Intelligence

Executive HR spend intelligence platform. Read-only system for C-level users.
It consolidates internal operational data, maps it into business objects,
computes monthly spend views, detects anomalies, and presents dashboard insight
plus AI-generated recommendations.

This file is the source of truth for system architecture. If another document
conflicts with this file, update the other document or resolve the conflict
before implementation continues.

Visual design source of truth: `DESIGN.md`

---

## Three rules that nothing overrides

**1. The application never writes back to the source system.**
The internal database is read-only input for v1. No approvals, no mutations,
no operational callbacks, no side effects into HerdHR or any upstream system.

**2. Deterministic analytics decide. The LLM narrates.**
Monthly totals, anomaly detection, rankings, and contributing-driver logic are
computed by application code first. The LLM receives structured facts and
returns explanation text only. It cannot invent metrics or replace analytics.

**3. Dashboard, export, and AI must use the same snapshot basis.**
The UI, Excel export, and generated summaries must all be tied to the same
refresh result. Never show one dataset in the dashboard and a different one in
the export or summary for the same user-visible snapshot.

---

## Stack

```text
Frontend        Next.js + TypeScript
Backend         FastAPI + Python
Primary DB      Application database for normalized ontology data,
                derived analytics, auth, and refresh metadata
Source System   Internal database, read-only
Jobs            Background worker for scheduled sync and summary generation
AI              LLM provider for natural-language summaries
Export          Excel export library
Auth            Simple email/password authentication for v1
```

---

## Architectural style

V1 is a modular monolith with asynchronous background jobs.

Why:

- simpler delivery than early microservices
- clear internal boundaries around sync, ontology, analytics, anomaly logic,
  AI summarization, and API delivery
- easier to evolve while requirements are still settling
- enough structure to extract workers or services later if scale demands it

The main split is:

- synchronous read APIs for dashboard, drill-down, export requests, and refresh
  status
- asynchronous job flow for sync, normalization, aggregation, anomaly
  recomputation, and AI summary generation

Modularity is a primary architectural goal, not only an implementation style.
The system should be partitioned into small, replaceable units with narrow
interfaces so that most business logic can be tested without booting the whole
application.

---

## Modularity rules

### Dependency direction

Dependencies must flow inward:

- UI -> API client -> API routes -> services -> repositories / external clients
- sync readers -> mappers -> ontology repositories
- analytics aggregators -> anomaly rules -> insight builders

Forbidden dependency patterns:

- UI components calling HTTP directly without adapter boundary
- route handlers containing business rules
- repositories calling other repositories to complete business workflows
- anomaly logic depending directly on HTTP, framework request objects, or UI
- AI prompt builders reaching back into source readers

### Small module rule

Each module should have one reason to change.

Preferred unit size:

- one route file per route group
- one service per use case or narrow use-case family
- one repository per aggregate or read-model family
- one mapper per source entity family
- one anomaly rule per anomaly type
- one export builder per workbook or sheet family

Avoid large “utility” or “service” files that mix unrelated rules.

### Naming and phase labels rule

Version labels such as `v3`, `v4`, and `v5` are planning-phase markers only.

Rules:

- use phase labels in docs, task trackers, and milestones only
- do not prefix runtime code, database tables, schemas, jobs, routes, or
  config keys with phase labels
- use domain names for implementation artifacts
- if an implementation artifact needs a lifecycle or rollout marker, name that
  marker after the business concept, not the project phase

Examples:

- good: `tenant_context`, `provisioning_jobs`, `backup_runs`
- bad: `v5_tenant_context`, `v3_uploads`, `v5_backup_runs`

### Ports and adapters rule

Framework and vendor details should stay at the edges.

Examples:

- FastAPI request/response objects stay in API layer
- database client details stay in repositories
- LLM SDK details stay in insight gateway/client code
- Excel library details stay in export builder layer

Core business logic should accept plain typed inputs and return plain typed
outputs.

### Snapshot isolation rule

Modules should exchange snapshot-scoped identifiers or typed read models,
not ad hoc shared mutable state.

This keeps refresh flow testable and prevents hidden coupling between stages.

## V2 guardrails from the completed V1 baseline

V1 is complete as a single-tenant product slice, but the codebase should not be
trapped in a forever-single-tenant shape.

These guardrails now apply to v2 planning and post-v1 changes.

### Tenant-aware seam rule

Even when runtime behavior is still single-tenant, architecture seams should
assume that a request or job belongs to a tenant context.

This does not mean full multi-tenant support is automatically in scope for v2.
It means new code should avoid assuming one permanent global dataset or one
permanent global storage target.

### Storage routing rule

Business services should not depend directly on one global database session as
an architectural assumption.

Use repository or storage-adapter boundaries so storage can later be routed per
tenant without rewriting business logic.

The current application may still resolve to one effective storage target.
That is acceptable as long as the code path does not hardcode that as a
permanent system rule.

### Logical storage-role rule

Treat product-owned storage as two logical roles, even if they still share one
physical database today:

- application storage for auth, config, job state, snapshot metadata, and
  operational application records
- analytics storage for normalized ontology data, derived metrics, anomalies,
  cached summaries, and export-ready read models

This keeps the code ready for future physical isolation or storage split
without forcing that complexity into the current runtime.

### Source isolation rule

Source-specific schema knowledge must stay inside source sync readers and
source-facing mapping boundaries.

Do not let analytics, API handlers, exports, or insight builders depend
directly on raw source tables or raw source naming.

Future connector-based ingestion depends on this isolation.

### No hidden global-state rule

Do not introduce caches, helpers, or shortcut query paths that silently assume
one global mutable dataset outside snapshot and orchestration boundaries.

Refresh, dashboard, export, and insight flows must remain snapshot-scoped and
replaceable by tenant-scoped storage later.

### Practical implication for v2 planning

When extending Insight Generation, Refresh Orchestration, Reporting and
Export, Data Store, and Quality Gates in v2:

- keep storage wiring centralized
- keep repository interfaces narrow
- keep analytics read models explicit
- keep refresh job sequencing owned by orchestration
- keep export and AI outputs bound to the same snapshot basis as dashboard data

These guardrails are architecture constraints, not a promise that every v2
feature must land immediately. They exist to reduce rewrite cost when tenant
isolation and connector expansion are introduced in later versions.

---

## Main runtime modules

### 1. Web Application

Responsibilities:

- provide executive dashboard pages
- handle login and authenticated user flows
- render summary metrics, trend charts, anomaly cards, and drill-down screens
- surface refresh status and last successful snapshot
- trigger export and manual refresh actions

Rules:

- all data access goes through typed frontend API clients
- components do not encode business analytics rules
- component folders stay reusable and canonical; do not create `-v2`,
  `-v3`, or similar versioned component folders/files
- when a component evolves, update the existing component in place or remove
  the obsolete one; keep only the live reusable surface
- UI follows `DESIGN.md`
- page containers orchestrate data fetching; presentational components stay
  dumb where possible
- chart and table data shaping should live in dedicated mapper or hook modules,
  not inline in page files

### 2. Application API

Responsibilities:

- expose typed HTTP APIs to the frontend
- validate auth and request payloads
- route requests to domain services
- keep response contracts stable

Rules:

- this layer stays thin
- no analytics formulas inside route handlers
- no direct dependency on raw source schema outside sync-facing code
- route handlers translate HTTP to typed service calls only
- route-level tests should not be the first place business logic is validated

### 3. Identity and Access

Responsibilities:

- manage simple email/password login for v1
- issue and validate authenticated sessions or tokens
- store minimal user identity and access metadata

V1 boundary:

- simple authentication only
- no advanced enterprise RBAC
- no row-level or tenant isolation design beyond authenticated access for the
  current product slice

### 4. Source Sync

Responsibilities:

- read source data from the internal database
- pull required HR and spend entities on a schedule
- support manual refresh initiation
- track sync status, timestamps, and failures

Rules:

- only this module knows the raw source schema in detail
- source access is read-only
- downstream code consumes normalized business objects, not raw tables
- each source entity family should have its own reader and mapper boundary

### 5. Semantic / Ontology Mapping

Responsibilities:

- convert raw source rows into normalized business objects
- preserve source lineage for audit and drill-down
- isolate source-specific naming from application-facing structures

Core v1 objects:

- Department
- Employee
- CostCenter
- ExpenseClaim
- PayrollExpense
- BudgetCode

Important boundary:

- claim expense and payroll expense remain separate object families
- executive spend views aggregate upward from them

### 6. Analytics Aggregation

Responsibilities:

- build monthly views used by dashboard and export
- aggregate spend by department, month, employee, and claim type
- provide efficient query-ready structures for executive analysis

Primary outputs:

- total payroll spend by month
- total claim spend by month
- department spend rankings
- month-over-month department deltas
- claim type contribution breakdowns
- employee contribution summaries where supported

### 7. Anomaly Detection

Responsibilities:

- detect unusual department spend changes
- detect unusually high claim expense patterns
- produce deterministic anomaly facts for UI and AI inputs

Rules:

- anomaly outputs must be explainable
- every anomaly record includes target, period, measured change, and supporting
  drill-down keys
- each anomaly rule should be implemented and tested independently

### 8. Insight Generation

Responsibilities:

- convert precomputed metrics and anomaly facts into executive summaries
- generate read-only recommendations
- keep summaries grounded in system-computed facts

Rules:

- no action execution
- no source-system write path
- summaries must reference the same refresh snapshot visible in the UI

### 9. Reporting and Export

Responsibilities:

- generate Excel exports aligned with dashboard-visible data
- package executive summary and breakdown data into downloadable output

Rules:

- export data comes from the same derived data basis as the UI
- no separate hidden reporting logic
- workbook assembly should be split from data retrieval so export formatting can
  be tested separately from query logic

### 10. Refresh Orchestration and Jobs

Responsibilities:

- run scheduled daily sync jobs
- run manual refresh jobs
- trigger normalization, aggregation, anomaly recomputation, and summary
  generation in the correct order
- track job state, completion, and failure

### 11. Application Data Store

Responsibilities:

- store source snapshots or staging records
- store normalized ontology objects
- store derived monthly aggregates
- store anomaly records
- store cached AI summaries
- store user auth data and refresh metadata

Logical zones:

- source snapshot or staging zone
- ontology zone
- analytics zone
- insight cache zone
- application metadata zone

---

## Data flow

### Ingestion flow

- Source Sync reads from the internal database
- raw records are written to staging or source snapshot storage
- Semantic / Ontology Mapping transforms them into normalized business objects

### Analytics flow

- Analytics Aggregation computes monthly spend views
- Anomaly Detection evaluates department-level change signals
- results are persisted for API and export use

### Insight flow

- Insight Generation receives precomputed facts
- it generates grounded executive summaries and recommendations
- summaries are stored for dashboard display and export inclusion

### User interaction flow

- user logs in
- frontend requests summary and drill-down data from the API
- API reads prepared analytics and insight results from the application store
- user can trigger export or manual refresh

### Manual refresh flow

- user invokes refresh from the UI
- API submits a refresh job
- orchestration runs sync -> normalize -> aggregate -> detect -> summarize
- frontend polls or reloads refresh status

---

## External interfaces

### Frontend to backend

Main API capability groups:

- auth
- summary
- departments
- trends
- anomalies
- drilldown
- exports
- refresh

Exact routes and payload schemas belong in detailed design.

### Backend to source system

- read-only internal database connection

This interface stays isolated behind Source Sync.

### Backend to LLM provider

- summarization request interface using structured, precomputed facts

The backend sends facts, not raw operational data with open-ended prompts.

---

## Cross-cutting concerns

### Auditability

- every executive metric must be traceable to source rows or derived aggregates
- every AI summary must be tied to the exact metrics and anomaly set that
  produced it

### Performance

- dashboard endpoints should read prepared monthly views where possible
- heavy sync and summarization work stays asynchronous

### Reliability

- sync and refresh jobs require explicit job-state tracking
- partial or failed refreshes must not silently overwrite the last known-good
  dashboard state

### Security

- auth uses standard password hashing and secure session or token handling
- source access stays read-only
- AI module cannot become a write path

### Observability

- record sync duration, failure reasons, and last successful refresh time
- record anomaly generation timing and AI summary generation errors

### Consistency

- export results and dashboard results come from the same derived data basis
- AI summaries align with the same snapshot the user is viewing

---

## Phase 1 boundary

Not in scope. Do not build. Do not scaffold placeholders.

- write-back into HerdHR or any operational source system
- triggered approvals or operational actions
- forecasting or predictive planning
- chat assistant workflows
- row-level or enterprise-grade access control
- real-time or near-real-time synchronization
- Excel import in the first production slice
- multi-source import beyond the internal database

---

## Testing architecture

Testing is part of the architecture, not optional cleanup.

The architecture should maximize the number of tests that can run as pure unit
tests with no framework boot, no network, and minimal fixture setup.

### Frontend tests

Must cover:

- component rendering for executive cards, anomaly cards, trend views, and
  drill-down states
- hook behavior for data fetching, loading, empty, and error states
- mapper/formatter utilities that transform API responses into UI-ready shapes
- page-level flows with mocked API responses
- manual refresh UX and export trigger behavior

Recommended split:

- unit tests for components, hooks, formatters, and API client adapters
- integration tests for page flows and key dashboard interactions
- prefer testing presentational components with plain props instead of mounting
  full pages when possible

### Backend tests

Must cover:

- schema validation and request/response contracts
- service-layer aggregation logic
- anomaly detection logic
- source-to-ontology mapping logic
- refresh orchestration sequencing
- AI summary input builder and fallback behavior
- auth flows and protected route behavior

Recommended split:

- unit tests for pure business logic and service helpers
- integration tests for API routes, persistence, refresh jobs, and export flow

Preferred test seam order:

1. pure function tests
2. service tests with mocked repositories and gateways
3. repository tests
4. route tests
5. end-to-end smoke tests

### Coverage priorities

Highest confidence required in:

- anomaly detection logic
- monthly aggregation logic
- ontology mapping logic
- snapshot consistency rules

The decision-making core should carry stricter coverage than thin framework
glue. Detailed thresholds belong in the detailed design and CI spec.
