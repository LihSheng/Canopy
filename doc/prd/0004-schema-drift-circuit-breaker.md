# PRD: Schema Drift Detection and Circuit Breaker

Status: ready-for-agent

## Problem Statement

Canopy imports datasets from third-party databases (PostgreSQL, MySQL). These upstream schemas are outside Canopy control. When a customer changes a column (remove/rename/type change), Canopy can fail late (during sync/materialization) or fail downstream (transformations), increasing MTTR and risk of silent data corruption.

Canopy needs an automated circuit breaker: detect source schema drift during discovery and sync runs, record the before/after delta, alert engineering/operations, and block affected datasets until reviewed.

## Solution

1. Store a **schema signature** per **source object** (`connection_id + source_object_name`), derived from normalized column schema (name + type details + nullability) and a stable hash.
2. During connection discovery and each relevant dataset sync run, re-discover the current schema, compare to the stored signature, and record a **schema drift event** when different.
3. Severity policy:
   - Breaking drift (`removed`, `renamed`, `type_change`) triggers a **schema drift block** by setting impacted datasets to `blocked_schema_drift` and skipping their sync runs.
   - Non-breaking drift (`added`) records an event and alerts, but does not block.
4. Emit “system alert” as persisted drift event + `audit_events` entry. Provide an extension point for future Slack/PagerDuty notifications.
5. UI surface in dataset workspace health panel via `GET /api/datasets/:id/health` drift status + a details endpoint listing recent drift events.

## User Stories

1. As an operator, I want Canopy to detect schema drift during discovery, so I can catch changes before scheduled sync runs.
2. As an operator, I want Canopy to detect schema drift during sync runs, so drift is caught even if discovery is not run manually.
3. As an engineer, I want drift events to show before/after schema, so I can quickly see what changed.
4. As an engineer, I want drift events to include a computed delta (added/removed/renamed/type change), so I can act without manual diffing.
5. As an operator, I want Canopy to block only the impacted datasets when breaking drift is detected, so unrelated datasets keep syncing.
6. As an operator, I want breaking drift to stop further sync/materialization work for impacted datasets, so constraints and mappings do not break later.
7. As a user, I want to see “schema drift detected” in the dataset workspace, so I understand why a dataset stopped updating.
8. As a user, I want to see whether the drift is breaking or non-breaking, so I can prioritize review.
9. As an operator, I want a clear “last drift detected at” timestamp, so I can correlate with upstream changes.
10. As an operator, I want a details view listing recent drift events per dataset/source object, so I can review history.
11. As an operator, I want a manual “clear schema drift block” action, so I can resume sync after review.
12. As a platform admin, I want drift events to appear in system audit logs, so the action is traceable.
13. As operations, I want drift alerts to be routable to Slack/PagerDuty in a later version, so incident response can be automated.
14. As an engineer, I want Canopy to detect nullability changes, so breaking changes like `NULL -> NOT NULL` are caught.
15. As an engineer, I want Canopy to detect string length changes, so truncation risk is visible.
16. As an engineer, I want Canopy to detect numeric precision/scale changes, so rounding/overflow risk is visible.
17. As an engineer, I want Canopy to detect timestamp timezone changes, so semantic time changes are caught.
18. As an operator, I want drift detection to be stable across dialect quirks (e.g. `int4` vs `integer`), so we avoid false positives.
19. As an engineer, I want added columns to be recorded but not block in v1, so pipelines keep moving while still informing us.
20. As an operator, I want drift to be recorded even on first discovery as a baseline without false “drift” spam, so onboarding is clean.

## Implementation Decisions

- Identity:
  - Store schema signature per `(connection_id, source_object_name)` (the source object).
- Signature fields:
  - Column name, nullability, normalized base type, plus type details:
    - strings: length
    - numeric: precision + scale
    - timestamps: timezone flag
  - Canonical JSON is order-independent (sorted) and hashed (stable hash).
- Drift classification:
  - Added, removed, renamed (best-effort), type change (includes nullable/length/precision/scale/tz).
  - Compute `is_breaking` if any removed/renamed/type change exists in delta.
- Persistence:
  - Add a schema signature table for current “last known” signature per source object.
  - Add a schema drift events table for immutable event history (before/after/delta, detected_by, timestamps, optional run/dataset linkage).
- Blocking:
  - Add `blocked_schema_drift` dataset status.
  - On breaking drift: update all datasets referencing that source object to `blocked_schema_drift`.
  - Sync engine must skip blocked datasets.
  - Add explicit “clear block” API for manual review workflow (v1 simple clear).
- Alerting:
  - “System alert” = persisted drift event + audit event types:
    - `schema_drift.detected`
    - `schema_drift.blocked_dataset`
    - `schema_drift.cleared`
  - Future outbound notifications via notifier interface + config-driven routing (not required in v1).
- API/UI:
  - Extend dataset health response with drift status and last drift timestamp.
  - Add dataset schema drift endpoint to list recent drift events.

## Testing Decisions

Good tests:
- Assert external behavior and observable outputs: given schemas A/B, the diff classification and breaking policy is correct; given breaking drift, datasets end up blocked and sync is skipped; given non-breaking drift, no block occurs.
- Avoid coupling to internal implementation details (exact SQL strings, internal helper methods), prefer pure function seams and service seams.

Modules to test:
- Schema normalization + hashing (pure).
- Drift diff algorithm (pure):
  - added column
  - removed column
  - type change (including nullable and type-detail fields)
- Service logic:
  - discovery compares signatures and records drift events
  - breaking drift triggers dataset blocking
  - sync preflight respects blocked status and performs compare
- API contracts:
  - dataset health returns drift fields when drift exists
  - drift listing endpoint returns recent events

Prior art:
- Backend unit and integration test patterns under the existing backend `tests/unit` and `tests/integration` suites.

## Out of Scope

- Full downstream transformation lineage blocking (dbt model-level blocking) beyond dataset-level block in v1.
- Automatic remediation (auto-mapping, auto-casting, auto-rename fixups).
- Constraint/index drift detection (PK/FK/indexes).
- Broad source types beyond PostgreSQL/MySQL for v1.
- UI catalog/list badges for drift/blocked status (health panel only in v1).

## Further Notes

- Later-version enhancements tracked in `doc/technical-notes/todo-schema-drift-followups.md`.
- Must respect ARCHITECTURE.md non-negotiables: never write back to source systems.
