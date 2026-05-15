# Refresh Orchestration Module Tasks

## Goal

Deliver asynchronous refresh with isolated stages, explicit publish semantics,
and safe preservation of the last known-good snapshot on failure.

## Tasks

- [ ] Define refresh job types, status enums, and stage enums.
- [ ] Implement `refresh_jobs` and `data_snapshots` persistence operations.
- [ ] Implement manual refresh request service.
- [ ] Implement stage command for `extract_source`.
- [ ] Implement stage command for `persist_snapshot`.
- [ ] Implement stage command for `normalize_ontology`.
- [ ] Implement stage command for `rebuild_aggregates`.
- [ ] Implement stage command for `detect_anomalies`.
- [ ] Implement stage command for `generate_insights`.
- [ ] Implement stage command for `publish_snapshot`.
- [ ] Implement worker orchestration for stage ordering and status transitions.
- [ ] Prevent partial snapshots from becoming current.
- [ ] Preserve last known-good snapshot on any failed stage.
- [ ] Expose current refresh status and job status reads.

## Testing

- [ ] Add backend unit tests for refresh status transition rules.
- [ ] Add backend unit tests for publish gating and snapshot-current logic.
- [ ] Add backend service tests for successful orchestration with mocked stage dependencies.
- [ ] Add backend service tests for failure handling and rollback-to-last-known-good behavior.
- [ ] Add backend integration tests for refresh job creation and status reads.
