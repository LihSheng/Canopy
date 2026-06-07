# Dataset Sync Error Handling

## Problem Statement

The dataset sync pipeline has silent failure paths that can produce incorrect results without the user knowing. Currently, when a data stream breaks mid-way during a sync, the system can report the sync as completed even though it only received partial data — or, in the worst case, it silently generates fake data as a fallback.

This means:
- A user sees their dashboard built on an incomplete snapshot, but no error is shown.
- A user expects fresh data, but the system is running on simulated events.
- The snapshot basis (dashboard, export, AI summary) is corrupted silently.

For an executive intelligence platform, silent data corruption is worse than a failed sync. A failed sync is visible. A corrupted snapshot is not.

## Solution

Make dataset sync failures visible and deterministic:

1. **Postgres batch sync**: When the data stream breaks mid-way, the error propagates to the sync orchestrator and marks the snapshot as `failed`. Partial data is never treated as complete.

2. **CDC streaming (real-time)**: Remove the simulation fallback entirely. When CDC streaming fails — whether the replication slot is missing, the connection drops, or the binlog is unavailable — the error propagates and produces a failed snapshot. No more fake events.

The user sees the same behavior in every environment: dev, staging, and production. A broken data source is always a failure, never a silent degradation.

## User Stories

1. As a platform engineer, I want Postgres batch sync to fail loudly when the connection drops mid-stream, so that I know the dataset is incomplete rather than discovering corrupted data in reports.

2. As a platform engineer, I want CDC streaming failures to produce a failed snapshot with an error message, so that I can investigate and resolve the root cause instead of unknowingly relying on simulated events.

3. As a platform engineer, I want the same error behavior in all environments (dev, staging, production), so that I can test failure handling locally and trust it works the same way in production.

4. As a platform engineer, I want the snapshot status to accurately reflect data integrity — `failed` when data is incomplete, not `completed` — so that downstream consumers (dashboard, export, AI) never serve partial data.

5. As a developer, I want the CDC reader code to be simpler and have no simulation fallback path, so that there is less code to maintain and no risk of accidentally enabling simulation in production.

6. As a platform engineer, I want sync error messages to include the root cause (connection failure, authentication error, stream interruption), so that I can diagnose issues without digging through logs.

## Implementation Decisions

### 1. Postgres adapter `fetch_table` error propagation

The Postgres `fetch_table` generator currently catches all exceptions silently via a bare `except: return` block. This means if the connection drops or the query fails mid-stream, the generator stops early and the caller receives partial data with no error indication.

**Decision:** Remove the bare `except: return` block. Errors propagate naturally out of the generator. The caller (`ExternalDbSyncService._sync_one`) already wraps the call in a `try/except` that produces a failed `EntitySnapshot` with the error message.

The MySQL adapter already follows this pattern — errors propagate to the caller. This change aligns Postgres with MySQL behavior.

### 2. CDC simulation fallback removal

Both `PostgresCdcReader` and `MysqlCdcReader` currently have a `_run_simulation()` method that generates fake mutation events as a fallback when real CDC is unavailable. Additionally, `PostgresCdcReader` has a mock environment check (`host == "localhost" and database == "testdb_mock"`) that skips real streaming and jumps directly to simulation.

**Decision:** Delete `_run_simulation()` from both readers entirely. Remove the mock environment branch. When CDC cannot connect or stream, the error propagates to the caller and produces a failed snapshot.

No environment-specific branching remains — the same code runs everywhere. Developers running locally without a real CDC source must either provide one or expect a failure, consistent with production behavior.

### 3. Sync result integrity

No schema changes are needed. The existing `EntitySnapshot` model already has a `status` field (`"completed"`, `"failed"`) and an `error_message` field. These gaps were at the adapter/reader layer, where errors were being consumed instead of propagated to this model.

### 4. Modules modified

- **Adapter layer** (`connection.adapters.postgres_adapter`): Error propagation in the `fetch_table` streaming generator
- **CDC readers** (`sync.readers.pg_cdc_reader`, `sync.readers.mysql_cdc_reader`): Remove simulation fallback, simplify to only production streaming path
- **Sync orchestration** (`sync.external_sync_service`): No logic changes — the error handling already exists here, it just wasn't receiving the errors

## Testing Decisions

### What makes a good test

Tests should verify external behavior (what the sync produces) not implementation details (how the adapter fetches rows). A good test:
- Sets up a scenario where data streaming fails
- Asserts that the sync result is marked as `failed`
- Asserts that the error message is non-empty and descriptive
- Does NOT assert which internal method was called or which exception type was raised

### Testing seams

**Seam 1 — `ExternalDbSyncService._sync_one` (highest seam):**
The entry point that calls adapters and CDC readers. Tests mock the adapter/reader and verify `_sync_one` returns the correct `EntitySnapshot`.
- Prior art: `tests/unit/test_external_sync_service.py` already mocks CDC readers

**Seam 2 — `DatabaseAdapter.fetch_table` generator (unit):**
Test that Postgres `fetch_table` propagates errors rather than swallowing them.
- Prior art: `tests/unit/test_sync_readers.py` has existing adapter tests

**Seam 3 — CDC reader `start_streaming` (unit):**
Test that connection failures propagate without simulation fallback.
- Prior art: `tests/unit/test_sync_readers.py` has existing CDC reader tests that patch `psycopg.AsyncConnection.connect`

### Existing simulation tests to remove

Approximately 28 test cases across `test_sync_readers.py` directly test simulation behavior (`_run_simulation`). These will be deleted and replaced with tests that verify error propagation.

## Out of Scope

- Retry logic with exponential backoff (future enhancement)
- Partial data detection via row count pre-fetching (future enhancement)
- Alerting or notification when syncs fail (depends on the existing operational health dashboard)
- Timeout configuration for streaming reads
- Changes to the `SyncResult` or `EntitySnapshot` schema
- Changes to the internal `SyncOrchestrator` (for internal source DB sync) — this path did not have the silent failure problem

## Further Notes

### CDC simulation was a dev-only convenience

The simulation fallback was originally added so developers could test CDC without a real database with logical replication enabled. This is now a hindrance because:
- It masks real failures during development
- There is no guard preventing simulation in staging/production
- It creates two code paths that diverge in behavior

The correct approach is to require a real CDC source for testing, or to mock at the seam level (as the existing unit tests do).
