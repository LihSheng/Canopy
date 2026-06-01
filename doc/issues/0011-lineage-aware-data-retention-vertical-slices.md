# Issues: Lineage-Aware Data Lifetime and Retention Policies

Status: draft

Parent: `doc/prd/0008-lineage-aware-data-retention.md`

These slices follow tracer-bullet shape: each issue should produce a narrow,
demoable path through persistence, service logic, API contract, UI behavior, and
tests. V1 is review-ready only; destructive purge stays out of scope.

1) **Dataset retention policy selector and admin save path**
- Type: AFK
- Blocked by: None
- User stories covered: 1, 2, 3, 6, 13, 18, 19
- What to build: Add tenant-scoped dataset retention policy ownership at dataset scope. Tenant admins can view and save product-neutral presets (`retain indefinitely`, `30 days`, `90 days`, `1 year`, `7 years`, `custom`) from the dataset workspace. The backend validates finite horizons, rejects destructive deletion inputs, records policy metadata, and writes an audit event for policy changes.
- Acceptance criteria:
  - [ ] Dataset workspace shows current retention policy, preset selector, custom horizon input, next calculated action date, and save/cancel states.
  - [ ] `GET /api/datasets/{id}/retention-policy` returns the current policy or default retain-indefinitely state.
  - [ ] `PUT /api/datasets/{id}/retention-policy` allows tenant admins to create, update, or disable policy state.
  - [ ] Non-admin users cannot create, update, or disable retention policies.
  - [ ] Finite policy horizons must be positive, and destructive deletion inputs are rejected as unsupported in v1.
  - [ ] Policy changes write audit records with tenant id, dataset id, actor id, event type, timestamp, and payload snapshot.
  - [ ] Backend unit/integration tests cover preset parsing, custom horizon validation, admin-only mutation, and audit creation.
  - [ ] Frontend tests cover selector rendering, validation errors, save success, and save failure.

2) **Finite policy impact preview and lineage warnings**
- Type: AFK
- Blocked by: Slice 1
- User stories covered: 4, 5, 14, 15
- What to build: Add a required impact preview flow for finite retention policies. The backend traverses downstream lineage from the root dataset and returns affected node ids, labels, types, calculated dates, and warning reasons. The UI requires a fresh preview before saving finite policies and highlights affected lineage nodes using API-supplied impact data. Downstream datasets do not automatically inherit stricter policies in v1.
- Acceptance criteria:
  - [ ] `POST /api/datasets/{id}/retention-policy/preview-impact` returns root dataset id, affected nodes, proposed root policy, calculated dates, and warning reasons.
  - [ ] Saving a finite policy requires a fresh impact preview unless the affected set is empty.
  - [ ] Downstream policy conflicts are shown as warnings only; no downstream policy is automatically changed.
  - [ ] Existing lineage UI highlights affected nodes from API data without component-local traversal logic.
  - [ ] Backend unit tests cover downstream traversal, empty impact sets, and warning-only conflict behavior.
  - [ ] Frontend tests cover preview drawer/panel, required-preview save blocking, warning display, and lineage highlighting.

3) **Retention lifecycle evaluator and active snapshot warning state**
- Type: AFK
- Blocked by: Slice 1
- User stories covered: 3, 10, 12, 19, 20
- What to build: Add deterministic lifecycle evaluation for dataset versions using materialized run completion time as the canonical expiry basis. Legacy dataset versions without materialized completion time fall back to dataset version creation timestamp and surface that fallback in preview/audit payloads. Active review-ready snapshots remain readable, with governance warning state exposed to dashboard/export/AI-facing read paths.
- Acceptance criteria:
  - [ ] Lifecycle evaluator calculates review dates from dataset version materialized run completion time.
  - [ ] Legacy fallback to dataset version creation timestamp is explicit in returned metadata and audit payloads.
  - [ ] Review-ready active versions stay readable and are not hidden or removed.
  - [ ] Dataset-facing responses expose governance warning state where active data is review-ready.
  - [ ] Dashboard, export, and AI read paths do not silently switch snapshot bases because of review-ready state.
  - [ ] Unit tests cover fixed UTC timestamp math, fallback behavior, and policy mode distinctions.
  - [ ] Regression tests cover active review-ready snapshot readability and warning state.

4) **Scheduled review-ready evaluation job and system audit**
- Type: AFK
- Blocked by: Slice 3
- User stories covered: 7, 8, 9, 11, 16, 17
- What to build: Add a scheduled retention evaluation job through the existing job/orchestration boundary. The job evaluates tenant-scoped datasets, marks eligible dataset versions and storage objects review-ready, persists affected counts and failures, and writes system-actor audit events. It does not delete data and does not expose user-triggered purge.
- Acceptance criteria:
  - [ ] Scheduled retention evaluation runs through the existing job boundary rather than a separate daemon stack.
  - [ ] Evaluation identifies expired or review-ready dataset versions and storage objects tenant by tenant.
  - [ ] Review-ready state is recorded without deleting data.
  - [ ] Storage lifecycle/retention markers reuse existing object storage guard and lifecycle concepts.
  - [ ] Job status, failure reason, and affected counts are persisted.
  - [ ] Audit records use a system actor and reference identifiers rather than copied row data.
  - [ ] No user-triggered purge or destructive evaluation endpoint exists in v1.
  - [ ] Integration tests cover scheduled evaluation, review-ready marking, job persistence, failure handling, and system audit events.

5) **Retention audit history and governance review surface**
- Type: AFK
- Blocked by: Slice 1, Slice 4
- User stories covered: 6, 7, 16, 17
- What to build: Add a dataset retention audit history API and UI surface so tenant admins and compliance reviewers can inspect policy changes, accepted previews, expiry detections, review-ready marks, and deferred purge decisions from the dataset workspace. Audit payloads should be identifier-based and not copy retained data.
- Acceptance criteria:
  - [ ] `GET /api/datasets/{id}/retention-policy/audit` returns policy and lifecycle events for the dataset in reverse chronological order.
  - [ ] Audit records include tenant id, dataset id, actor id or system actor, event type, timestamp, and payload snapshot.
  - [ ] Audit payloads reference dataset/version/storage identifiers and do not copy raw data.
  - [ ] Dataset workspace exposes a retention audit panel with empty, loading, error, and populated states.
  - [ ] Audit panel clearly distinguishes tenant-admin events from scheduled system events.
  - [ ] Backend integration tests cover audit access, event ordering, and tenant scoping.
  - [ ] Frontend tests cover audit history rendering and error states.

6) **Snapshot consistency regression gate for retention lifecycle states**
- Type: AFK
- Blocked by: Slice 3, Slice 4
- User stories covered: 12, 20
- What to build: Add a focused regression gate proving dashboard, export, and AI summary paths remain snapshot-consistent when a dataset version is review-ready. Active review-ready snapshots stay readable with warnings; future purged/deleted states are not selected as active snapshot bases.
- Acceptance criteria:
  - [ ] Dashboard data stays tied to the active snapshot when that snapshot is review-ready.
  - [ ] Export data stays tied to the same snapshot basis as the dashboard.
  - [ ] AI summary inputs stay tied to the same snapshot basis as dashboard/export.
  - [ ] Review-ready warning state is visible where relevant and does not alter metrics.
  - [ ] Future purged/deleted lifecycle states are rejected as active snapshot candidates.
  - [ ] Regression tests cover dashboard/export/AI snapshot consistency for active review-ready data.

## Publishing Notes

- Issue tracker publishing is not performed from this draft because tracker
  configuration and triage label vocabulary were not provided in this thread.
- If publishing later, apply `needs-triage` to each issue and publish in
  dependency order: Slice 1, Slice 2, Slice 3, Slice 4, Slice 5, Slice 6.
