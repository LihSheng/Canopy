# PRD: Lineage-Aware Data Lifetime and Retention Policies
Status: Draft

## Problem Statement

Canopy now has dataset workspaces, immutable dataset versions, lineage views,
tenant-scoped storage, object lifecycle state, and audit-oriented platform
boundaries. What is missing is a product-level way for operators to define how
long dataset data should live and understand which downstream datasets, versions,
storage objects, and lineage nodes will be affected before a purge workflow
runs.

Without this feature, expired or obsolete data can remain active across raw
storage, derived dataset versions, and lineage-connected outputs. That weakens
governance, makes retention behavior manual, and leaves operators without a
clear blast-radius view before data lifecycle actions.

## Solution

Add a tenant-scoped retention policy module for datasets:

- dataset settings expose a data lifetime policy selector
- policy preview shows downstream lineage impact before save or execution
- backend calculates expiry and review dates from immutable dataset version and
  storage metadata
- scheduled retention workflow identifies expired dataset versions and storage
  objects for lifecycle review
- all policy changes, preview decisions, expiry detections, review-ready marks,
  and explicitly deferred purge decisions are auditable

The feature must preserve the architecture rules:

- no write-back into upstream source systems
- deterministic backend logic decides expiry and purge eligibility
- dashboard, export, and AI continue to bind to snapshot-scoped data and must
  not silently switch to partially purged data

## User Stories

1. As a dataset operator, I want to assign a retention policy to a dataset, so
   that data lifetime is explicit.
2. As a dataset operator, I want predefined lifetime options, so that common
   policy choices are consistent.
3. As a dataset operator, I want to see the calculated expiry or review date, so
   that I understand when action will be needed.
4. As a dataset operator, I want to preview downstream lineage impact, so that I
   do not accidentally invalidate dependent datasets.
5. As a dataset operator, I want affected lineage nodes highlighted, so that the
   blast radius is visible in the existing lineage UI.
6. As a dataset operator, I want retention policy changes audited, so that there
   is a history of who changed lifecycle behavior.
7. As a compliance reviewer, I want purge and review decisions audited, so that
   data lifecycle actions are explainable.
8. As a platform operator, I want a scheduled workflow to identify expired data,
   so that retention does not depend on manual browsing.
9. As a platform operator, I want expired data to be marked review-ready, so
   that destructive action is deferred until active-snapshot fallback rules are
   explicit.
10. As an engineer, I want policy logic separated from routes and UI, so that
    expiry math and lineage traversal are unit-testable.
11. As an engineer, I want retention lifecycle changes to use the existing
    object storage guard and lifecycle states, so that tenant isolation remains
    intact and future deletion work has a safe boundary.
12. As an executive dashboard user, I want active dashboards and exports to stay
    tied to valid snapshots, so that purged data does not create hidden
    inconsistency.
13. As a tenant admin, I want only admins to change retention policies, so that
    lifecycle governance is not changed by normal dataset viewers.
14. As a tenant admin, I want finite policies to require impact preview, so that
    downstream effects are acknowledged before save.
15. As a downstream dataset owner, I want upstream retention conflicts surfaced
    as warnings, so that my dataset behavior is not silently changed by another
    dataset policy.
16. As a platform operator, I want scheduled retention evaluation to persist
    affected counts and failures, so that I can diagnose job behavior.
17. As a compliance reviewer, I want audit payloads to reference identifiers
    instead of copied data, so that the audit trail does not create another data
    retention problem.
18. As a product owner, I want product-neutral presets, so that the UI does not
    imply legal guarantees that the product has not modeled.
19. As a QA engineer, I want expiry math tested with fixed UTC timestamps, so
    that retention behavior does not drift with local time zones.
20. As an engineer, I want active review-ready snapshots to remain readable, so
    that dashboard, export, and AI snapshot consistency does not break before
    purge design exists.

## Functional Requirements

### Dataset Policy Management

- Add a dataset-level retention policy configuration surface in the existing
  dataset workspace, preferably under the current `Details` area unless a
  dedicated governance tab is introduced.
- Supported initial policy modes:
  - retain indefinitely
  - expire after a fixed number of days
  - review required after a fixed number of days
- Supported v1 presets are product-neutral only:
  - retain indefinitely
  - 30 days
  - 90 days
  - 1 year
  - 7 years
  - custom
- V1 must not use regulatory labels such as GDPR or CCPA until legal semantics
  are explicitly modeled.
- Store policy state tenant-scoped and dataset-scoped.
- The dataset is the policy ownership root. Dataset versions, storage objects,
  and downstream lineage nodes are computed targets, not independent policy
  owners in v1.
- Only tenant admins may create, update, or disable retention policies.
- Record policy author, timestamps, active/inactive state, and latest calculated
  expiry or review date.
- Validate policy input with deterministic rules:
  - horizon days must be positive when a finite policy is selected
  - destructive deletion inputs must be rejected as unsupported in v1
  - policy changes must not bypass tenant access checks

### Lineage Impact Preview

- Add a preview operation that starts from a dataset and traverses downstream
  lineage using existing dataset lineage concepts.
- Preview response must include:
  - root dataset id
  - affected node ids and labels
  - affected node types
  - policy proposed at the root dataset
  - calculated expiry or review date where available
  - reason each node is affected
- V1 does not automatically inherit stricter policy into downstream datasets.
  Downstream impact is previewed and warned only.
- The existing lineage UI should render affected nodes with clear warning
  styling and no hidden business logic in the component.
- Saving a finite retention policy should require a fresh impact preview unless
  the affected set is empty.

### Expiry Calculation

- Expiry math is deterministic backend service logic.
- Initial expiry basis is dataset version materialized run completion time, not
  current wall-clock save time, source record timestamp, or storage object
  creation time.
- If a legacy dataset version does not have a materialized run completion time,
  the service must use the dataset version creation timestamp as a fallback and
  mark that fallback in the preview/audit payload.
- The workflow must distinguish:
  - policy configured
  - data eligible for review
  - data marked expired
  - purge explicitly deferred
- Expiry state must not mutate upstream source systems.

### Scheduled Retention Workflow

- Add a scheduled job through the existing job/orchestration boundary rather
  than introducing an unrelated daemon stack.
- The job identifies expired or review-ready dataset versions and storage
  objects tenant by tenant.
- The first release records review-ready state and does not delete data.
- Only the system scheduled job may mark data review-ready in v1.
- No user-triggered purge exists in v1.
- Destructive purge is deferred until active-snapshot replacement and rollback
  rules are defined.
- Job status, failures, and affected counts must be persisted.

### Auditability

- Audit records must cover:
  - policy create/update/disable
  - impact preview accepted before save
  - expiry detected
  - review-ready marked
  - deferred purge explicitly not executed
- Audit entries must include tenant id, dataset id, actor id or system actor,
  event type, timestamp, and payload snapshot.
- Policy changes use the authenticated tenant admin as actor. Scheduled
  retention evaluation uses a system actor.
- Audit payloads should reference dataset/version/storage identifiers, not raw
  copied data.

### Snapshot and Dashboard Consistency

- If a dataset version becomes expired or deleted, dashboard/export/AI flows must
  not read it as an active snapshot.
- If an active dataset version is review-ready in v1, dashboard/export/AI flows
  may keep reading it, but must surface governance warning state where relevant.
- The system must preserve last known-good behavior for user-visible snapshots:
  failed or partial purge workflows must not silently produce mixed dashboard,
  export, and AI bases.
- V1 must not hide or remove an active review-ready snapshot until a replacement
  snapshot exists and explicit purge design is implemented.

## Implementation Decisions

### Deep Modules

- Retention Policy Service owns policy validation, tenant-scoped policy writes,
  preset handling, and admin-only mutation rules.
- Retention Lifecycle Evaluator owns deterministic expiry/review math from
  dataset version materialized run completion time, including legacy fallback
  handling.
- Lineage Impact Service owns downstream traversal and conflict/warning output
  so the UI renders supplied impact data instead of recomputing graph rules.
- Retention Evaluation Job owns scheduled review-ready detection, affected-count
  persistence, failure recording, and system-actor audit events.
- Audit Integration owns append-only policy and lifecycle event recording using
  identifiers and payload snapshots, not copied row data.
- Dataset Governance UI owns policy selection, preview confirmation, lifecycle
  status display, and lineage warning presentation.

### Architecture and Boundaries

- Follow existing API route conventions. Do not add `/api/v1` only for this
  feature.
- Keep policy business logic in a retention/governance service layer, not in API
  route handlers.
- Use tenant-scoped persistence consistent with the multi-tenant platform.
- Model retention policy ownership at dataset scope. Version-level and
  storage-level records should store evaluated lifecycle state and policy
  references, not separate editable policy definitions.
- Do not automatically propagate stricter policies to downstream datasets in
  v1. Treat downstream policy conflicts as warning/decision data for operators.
- Restrict policy mutation to tenant admins. Restrict review-ready marking to
  scheduled system execution. Do not expose user-triggered purge in v1.
- Keep active review-ready snapshots readable in v1. Surface warning state, but
  do not hide or remove them without a replacement snapshot and a later purge
  design.
- Use product-neutral retention presets only in v1. Avoid named
  legal-regulatory templates until policy semantics, jurisdiction, and legal
  ownership are defined.
- Reuse existing lineage concepts exposed by `GET /api/datasets/{id}/lineage`
  where possible, but extend the service model if downstream traversal requires
  persisted lineage metadata beyond the current synthetic dataset graph.
- Reuse existing storage lifecycle states (`active`, `archived`, `expired`) and
  retention states (`retained`, `deletable`) for review markers before adding
  new object-storage concepts.
- Reuse existing audit service patterns where available instead of creating a
  separate audit subsystem.
- Keep destructive purge out of v1. Upstream sources remain read-only.
- Keep LLM involvement out of retention decisions. AI may narrate governance
  status later, but deterministic services decide lifecycle state.

## API Requirements

Candidate endpoints:

- `GET /api/datasets/{id}/retention-policy`
- `PUT /api/datasets/{id}/retention-policy`
- `POST /api/datasets/{id}/retention-policy/preview-impact`
- `GET /api/datasets/{id}/retention-policy/audit`
- scheduled retention evaluation should run through the existing job boundary;
  v1 should not expose user-triggered purge or destructive evaluation endpoints

Response contracts should be typed and stable. Routes should only validate HTTP
input, resolve auth/tenant context, and call service methods.

## UI Requirements

- Add retention controls to the dataset workspace.
- Show current policy, calculated next action date, and current lifecycle state.
- Show preview drawer or panel listing affected downstream lineage nodes.
- Highlight affected nodes in `LineageView` using data supplied by API
  responses, not component-local traversal logic.
- Provide loading, empty, validation-error, and save-failure states.
- Use existing design language and status badge conventions from
  `ARCHITECTURE.md`.

## Testing Decisions

- Good tests assert externally visible lifecycle behavior, authorization,
  snapshot consistency, and audit output. They should avoid coupling to private
  helper names or UI implementation structure.
- Unit-test expiry calculation with fixed UTC timestamps.
- Unit-test lineage impact traversal with small explicit graphs.
- Unit-test policy validation separately from API route tests.
- Unit-test preset parsing and custom horizon validation.
- Unit-test admin-only mutation decisions.
- Integration-test dataset retention endpoints with tenant-scoped data.
- Integration-test scheduled evaluation against seeded dataset versions and
  storage objects.
- Integration-test audit creation for policy changes and purge workflow events.
- Integration-test that normal users cannot create, update, or disable policies.
- Frontend-test the policy selector, impact preview, and lineage highlighting
  with mocked API payloads.
- Frontend-test governance warning display for active review-ready snapshots.
- Regression-test that expired/deleted versions are not selected as active
  dashboard/export/AI snapshot bases.

## Acceptance Criteria

1. Dataset workspace exposes a configurable data lifetime policy selector.
2. Saving a finite policy requires backend validation and writes an audit event.
3. Users can preview downstream lineage impact before applying a finite policy.
4. The lineage view highlights affected downstream nodes from the preview data.
5. The backend calculates expiry or review dates from stored dataset/version
   timestamps and policy horizon.
6. Scheduled retention evaluation identifies expired or review-ready data across
   tenant-scoped datasets.
7. Review-ready workflows mark eligible storage objects without cleanup.
8. V1 retention workflows do not delete data automatically.
9. Retention policy and review-ready events are auditable with tenant, actor,
   dataset, and event payload metadata.
10. Dashboard, export, and AI summaries keep active review-ready snapshots
    readable with governance warning state, and future purged/deleted versions
    are never selected as active snapshot bases.

## Out of Scope

- Write-back to upstream source systems.
- Regulatory legal advice or jurisdiction-specific compliance guarantees.
- Chat assistant workflows for governance.
- Forecasting future storage growth.
- New third-party orchestration stack if existing job infrastructure can support
  scheduled evaluation.
- Destructive purge execution; v1 only marks data review-ready.
- Column-level masking or anonymization unless a separate data-classification
  model is defined first.
- Cross-tenant global retention administration.
- Real-time retention enforcement on every row write.

## Resolved Clarifications

1. Resolved: the first release only marks data review-ready. Destructive purge
   is deferred until active-snapshot fallback, approval, and rollback rules are
   explicit.
2. Resolved: the canonical expiry basis is dataset version materialized run
   completion time. Dataset version creation timestamp is only a legacy fallback
   and must be surfaced in preview/audit payloads.
3. Resolved: retention policy attaches to the dataset as the user-facing
   ownership root. Dataset versions, storage objects, and downstream lineage
   nodes are computed execution/impact targets.
4. Resolved: downstream datasets do not automatically inherit stricter policies
   in v1. The system previews and warns about affected downstream nodes only.
5. Resolved: only tenant admins may configure policies. Only the system
   scheduled job may mark data review-ready. No user-triggered purge exists in
   v1.
6. Resolved: if the active dashboard snapshot is review-ready, keep it readable
   and surface governance warning state. Do not hide or remove it until a
   replacement snapshot exists and explicit purge design lands.
7. Resolved by question 1: v1 needs lifecycle review-ready marking plus audit,
   not hard purge.
8. Resolved: v1 presets are product-neutral only: retain indefinitely, 30 days,
   90 days, 1 year, 7 years, and custom. No GDPR/CCPA-style labels until legal
   semantics are explicitly modeled.

## Further Notes

- This PRD intentionally stops short of destructive purge. That is not a gap; it
  is the safety boundary for the first implementation slice.
- The existing per-dataset configuration model is consistent with retention
  policy ownership at dataset scope.
- Review-ready state is a governance signal, not a data removal action.
- If later work adds destructive purge, it needs a separate PRD or ADR covering
  active snapshot replacement, rollback, approval, and operator execution paths.
