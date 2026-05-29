# PRD: Centralized Operational Health & Pipeline Data Health Dashboard
Status: Draft

## Problem Statement

Engineering operators need a single place to see operational health across pipelines and datasets, detect failures early, and drill into the blast radius. Current runtime state is transient and not sufficient for a rolling window view or auditability.

## Solution

Provide an admin-only engineering dashboard that summarizes data health across pipelines over a rolling 30-day window, backed by persisted telemetry and daily rollups. The dashboard surfaces top-level KPIs (latency vs thresholds, bytes written, error counts), trend charts, and drill-down tables for recent failed runs and affected datasets/pipelines.

## User Stories

1. As an admin user, I want to see top-level operational KPIs for the last 30 days, so that I can judge overall system health at a glance.
2. As an admin user, I want to view total bytes written aggregated across pipelines, so that I can spot throughput changes and unexpected volume shifts.
3. As an admin user, I want to view rolling error counts over the last 30 days, so that I can detect regressions and instability.
4. As an admin user, I want to view SLA latency violation rate/count, so that I can detect performance degradations.
5. As an admin user, I want to see a trend chart for bytes written over the last 30 days, so that I can understand throughput directionality.
6. As an admin user, I want to see a trend chart for errors over the last 30 days, so that I can identify days with elevated failure rates.
7. As an admin user, I want to see a trend chart for SLA violations over the last 30 days, so that I can understand latency health over time.
8. As an admin user, I want to filter pipelines by health state (healthy/degraded/failed), so that I can focus on issues first.
9. As an admin user, I want to drill into a pipeline row, so that I can see that pipeline’s 30-day summary and recent runs.
10. As an admin user, I want to see a table of recent failed runs, so that I can respond quickly to active incidents.
11. As an admin user, I want to open a run detail view, so that I can see step timeline, error message, and telemetry fields for diagnosis.
12. As an admin user, I want to drill from aggregate metrics to affected datasets, so that I can scope blast radius.
13. As an admin user, I want metrics to persist across worker restarts and infrastructure reboots, so that history is reliable.
14. As an admin user, I want the dashboard to be tenant-scoped, so that I only see data for the active tenant context.
15. As an admin user, I want “source” breakdowns, so that I can attribute bytes/errors to specific upstream connections.
16. As an admin user, I want the 30-day window to be consistent and predictable, so that charts and counts match across page reloads.
17. As an admin user, I want “warnings” tracked separately from “errors”, so that I can distinguish degradations from hard failures.
18. As an admin user, I want API responses to be fast under high telemetry volume, so that the dashboard stays responsive.
19. As an admin user, I want the UI to hide admin navigation for non-admin users, so that access is obvious and clean.
20. As an admin user, I want a clear system-level status indicator, so that I can quickly see if anything is failed or degraded.

## Implementation Decisions

- Access control
  - Admin-only feature gate using the existing admin flag.
  - UI gating uses session data to show/hide admin navigation, but backend remains the source of truth for authorization.

- Tenancy and scoping
  - All metrics are tenant-scoped to the active tenant context (no cross-tenant global view in v1).

- Windowing and time semantics
  - Rolling window defaults to 30 days and is computed using UTC timestamps.
  - Trend buckets are per UTC date (daily resolution in v1).

- Canonical identifiers
  - Define a stable `pipeline_id` in v1 using job type and dataset when applicable:
    - dataset-scoped: `{job_type}:{dataset_id}`
    - tenant/global: `{job_type}`
  - Store `dataset_id` when applicable.
  - Define “source” as `connection_id` for grouping and drill-down.

- Telemetry persistence model
  - Persist immutable telemetry rows for pipeline run steps with:
    - duration, bytes written, status, error message (when failed), timestamps, identifiers (pipeline/dataset/connection)
  - Emit telemetry at step terminal states (success/failed), with optional heartbeats for long-running steps.
  - Persist the latency threshold snapshot into telemetry rows so historical comparisons remain stable if thresholds change later.

- Error/warning semantics
  - Top-level “rolling_error_count” counts failed telemetry steps (and failed job runs for non-dataset jobs) over the window.
  - Track warnings separately as “warnings_30d” (not counted as errors in the headline KPI).

- Bytes written semantics
  - Bytes written is sourced from telemetry (persisted at step end), attributed to pipeline/dataset/source as above.
  - If a run creates storage objects, telemetry should reflect the bytes written so rollups do not require re-deriving from storage.

- Rollups and query performance
  - Implement daily rollups to power fast trend queries and top-level KPIs.
  - Keep raw telemetry for a limited retention window; keep rollups indefinitely.
  - Aggregation job runs hourly and upserts recent rollup days (today and yesterday) to handle late-arriving events.
  - Provide an operator-triggered backfill to populate the last 30 days quickly on first deploy.

- Health state derivation (v1)
  - Pipeline states:
    - FAILED: any failure in the last 24 hours
    - DEGRADED: no failures in last 24 hours, but SLA violation in last 7 days or any failures within the 30-day window
    - HEALTHY: otherwise
  - System status:
    - FAILED if any pipeline is FAILED
    - WARNING if none failed but at least one DEGRADED
    - HEALTHY otherwise

- API surface (admin)
  - Provide endpoints for:
    - summary KPIs for a rolling window
    - daily trends for a selected metric type
    - pipeline catalog with health state and 30-day aggregates
    - run-level drill-down for recent failures and pipeline detail views
  - Follow existing API routing conventions (no new versioned prefix for v1).

- UI scope and drill-down
  - Admin area contains data health only in v1.
  - Drill-down stays within the admin dashboard (pipeline detail + run detail drawer/page).
  - Deep-link to lineage visualization is explicitly deferred unless it is already cheap to wire.

## Testing Decisions

- Good tests assert observable behavior:
  - correct windowing semantics (UTC, 30-day rolling)
  - correct aggregation math for bytes/errors/SLA violations
  - correct admin-only authorization behavior
  - drill-down routing and filtering behavior from aggregate → pipeline → run

- Backend tests
  - Unit tests for rollup aggregation logic (pure inputs → outputs).
  - Integration tests for admin endpoints against a test database with seeded telemetry and rollups.
  - Authorization tests verifying non-admin rejection.

- Frontend tests
  - Unit tests for KPI cards and chart mappers/formatters given API payloads.
  - Integration tests for admin page flows with mocked API responses (loading/empty/error states + drill-down interactions).

## Out of Scope

- Cross-tenant/global super-admin view spanning all tenants.
- Near-real-time SLAs and sub-daily rollups (5-minute/hourly buckets).
- Operational write-backs or remediation actions from the dashboard.
- Lineage canvas deep-linking and schema-delta visualizations (unless separately scoped).
- External telemetry ingestion from third-party orchestrators not already owned by Canopy runtime.

## Further Notes

- Metrics must be backed by persisted telemetry and rollups, not only live worker memory state.
- Retention target: raw telemetry retained for 90 days; daily rollups retained indefinitely.
- The dashboard is an engineering/admin tool and must remain compatible with the system’s read-only stance toward upstream source systems.

