# Refresh Orchestration Module Tasks

## Goal

Deliver asynchronous refresh with isolated stages, explicit publish semantics,
and safe preservation of the last known-good snapshot on failure.

## Tasks

- [x] Define refresh job types, status enums, and stage enums.
- [x] Implement `refresh_jobs` and `data_snapshots` persistence operations.
- [x] Implement manual refresh request service.
- [x] Implement stage command for `extract_source`.
- [x] Implement stage command for `persist_snapshot`.
- [x] Implement stage command for `normalize_ontology`.
- [x] Implement stage command for `rebuild_aggregates`.
- [x] Implement stage command for `detect_anomalies`.
- [x] Implement stage command for `generate_insights`.
- [x] Implement stage command for `publish_snapshot`.
- [x] Implement worker orchestration for stage ordering and status transitions.
- [x] Prevent partial snapshots from becoming current.
- [x] Preserve last known-good snapshot on any failed stage.
- [x] Expose current refresh status and job status reads.

## Testing

- [x] Add backend unit tests for refresh status transition rules.
- [x] Add backend unit tests for publish gating and snapshot-current logic.
- [x] Add backend service tests for successful orchestration with mocked stage dependencies.
- [x] Add backend service tests for failure handling and rollback-to-last-known-good behavior.
- [x] Add backend integration tests for refresh job creation and status reads.
