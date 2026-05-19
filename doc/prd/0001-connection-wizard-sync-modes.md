# PRD: Connection Wizard with Per-Dataset Sync Modes

Status: ready-for-agent

## Problem Statement

Today, Canopy Intelligence connects to a single internal database and pulls all data on one schedule. Users who want to bring in data from external databases (Postgres, Oracle, MySQL) have no way to connect them. Users who manage both small lookup tables and multi-million-row transaction tables have no way to tune the sync strategy. They are forced to pull everything fresh every time, placing unnecessary load on the source system. Users with sensitive data that must never leave their infrastructure have no option to query it live without copying.

The system needs to become a multi-connector data hub where users can connect external databases, pick which tables to import, and choose per table how data should move: on a schedule (batch), near-real-time (streaming), or not at all (live query).

## Solution

A Connection Wizard in the Data Studio section of the analytics shell. The wizard walks users through three steps:

1. Authenticate: enter host, port, database name, username, and password; test the connection before proceeding.
2. Select Objects: browse discovered tables with row counts and column schemas; check the ones to import.
3. Configure Sync Policy: for each selected table, choose a sync mode (Batch, Real-Time, or Direct View) and, for Batch tables, a strategy (Full Snapshot or Incremental Cursor) with an auto-detected cursor column.

After the wizard completes, the user sees their connections and datasets in the Data Studio catalog. Each dataset shows its sync mode badge, last sync time, and row count. Batch and Real-Time datasets participate in the existing refresh pipeline. Direct View datasets are routed to a separate Live Explorer module (future) and never mix with snapshot-consistent dashboards, exports, or AI summaries.

Third-party database credentials are encrypted at rest via a SecretStore interface (AES-256-GCM with an application key), designed for a future swap to AWS Secrets Manager.

## User Stories

### Connection Discovery and Setup

1. As a data engineer, I want to see a list of supported source types (PostgreSQL, MySQL, etc.) before I begin, so that I know which external databases I can connect.

2. As a data engineer, I want to enter my external database credentials (host, port, database name, username, password) and click "Test Connection," so that I know immediately whether the credentials are valid without committing to a full import.

3. As a data engineer, I want the system to show me a clear success or failure message after the connection test, so that I can fix typos or network issues before proceeding.

4. As a data engineer, I want my credentials to be encrypted before storage, so that a database dump or debug log does not expose my external database passwords.

5. As a data engineer, I want to give the connection a memorable name, so that I can tell it apart from other connections later in the catalog.

### Table Discovery and Selection

6. As a data engineer, I want the system to automatically discover all tables in my external database and show their names and estimated row counts, so that I don't have to type table names manually.

7. As a data engineer, I want to preview a table's column names and data types by clicking on it, so that I can verify I'm selecting the right table before importing.

8. As a data engineer, I want to see sample rows (first 10) from a table, so that I can confirm the data looks correct.

9. As a data engineer, I want to search or filter the table list, so that I can quickly find a specific table in a database with hundreds of tables.

10. As a data engineer, I want a "Select All" toggle, so that I can quickly check all tables when the database has only a few.

11. As a data engineer, I want to see a running count of how many tables I have selected, so that I don't lose track when working through a long list.

### Sync Policy Configuration

12. As a data engineer, I want to choose a sync mode per table (Batch, Real-Time, or Direct View), so that I can apply the right strategy to each table based on its size, freshness requirements, and sensitivity.

13. As a data engineer, I want to select "Batch" for small lookup tables and configure "Full Snapshot" (wipe and repull), so that the entire table is refreshed cleanly every time.

14. As a data engineer, I want to select "Batch" for large transaction tables and configure "Incremental Cursor" (only pull rows changed since last sync), so that I reduce load on my source database.

15. As a data engineer, I want the system to auto-detect the best cursor column (e.g., updated_at) and show me which column it found with a clear badge, so that I don't have to inspect schema manually in 80% of cases.

16. As a data engineer, I want to override the auto-detected cursor column by picking from a dropdown of all timestamp columns, so that I can correct the system when it picks the wrong column.

17. As a data engineer, I want to see a warning when no common cursor column is auto-detected, so that I know I must pick one manually before proceeding.

18. As a data engineer, I want to set a sync frequency for Batch datasets (e.g., every 1 hour, every 24 hours), so that I control how often the source database is queried.

19. As a data engineer, I want to select "Real-Time" for operational tables that change constantly, so that my dashboards reflect near-real-time data (currently via accelerated polling, with CDC infrastructure planned for the future).

20. As a data engineer, I want to select "Direct View" for tables containing sensitive data that must not be copied into Canopy Intelligence storage, so that queries run live against the source and no data is persisted.

### Post-Wizard Catalog and Management

21. As a data engineer, I want to see all my connections listed in the Data Studio catalog with status badges (active, paused, error), so that I can monitor my data pipeline at a glance.

22. As a data engineer, I want to click into a connection to see its child datasets, each showing its sync mode, last sync timestamp, and row count, so that I can verify that data is flowing as expected.

23. As a data engineer, I want to edit a dataset's sync policy after the wizard is complete (change sync mode, strategy, frequency, or cursor column), so that I can adjust as my needs evolve.

24. As a data engineer, I want the system to force a full re-pull when I change a dataset's cursor column, so that no rows are missed after the switch.

25. As a data engineer, I want to manually trigger a re-import for a specific dataset, so that I can refresh data on demand without waiting for the schedule.

26. As a data engineer, I want to see a dataset's version history (past import runs with timestamps, row counts, and status), so that I can audit when data was last refreshed and whether any versions failed.

### Dashboard Integration

27. As an executive, I want the existing Dashboard, Departments, Anomalies, and Reports pages to continue showing snapshot-consistent data regardless of which sync mode feeds each dataset, so that I always see a coherent view.

28. As an executive, I want each dashboard card to show a Data Freshness Widget with "Last updated X minutes ago," so that I know how fresh the data is.

29. As an executive, I want to be able to trigger a manual refresh of all Batch and Real-Time datasets from the dashboard, so that I can get the latest data without waiting for a schedule.

### Security and Future-Proofing

30. As a platform operator, I want the credential encryption key to be configurable via an environment variable, so that I can rotate it without code changes.

31. As a platform operator, I want the SecretStore interface to have a clear migration path to AWS Secrets Manager, so that when we move to production we can swap implementations without schema changes or service rewrites.

32. As a platform operator, I want Direct View datasets to never appear in exports or AI summaries, so that sensitive live-queried data is not accidentally leaked into downloaded files or LLM prompts.

## Implementation Decisions

### Architecture

- **Per-dataset sync mode (ADR-0001).** The sync_mode field lives on the Dataset domain aggregate, not on Connection. Each table in a connection can have its own sync mode. This matches the user's mental model of per-table configuration in the Connection Wizard.

- **SecretStore encryption boundary (ADR-0002).** Third-party database credentials are encrypted with AES-256-GCM using an application key. The encryption lives behind a SecretStore abstract interface (encrypt/decrypt) so AWS Secrets Manager can be swapped in later by implementing the same interface.

- **Direct Query isolation.** Direct Query datasets are never pulled by the refresh pipeline and never feed the executive dashboard, exports, or AI summaries. They will live in a separate Live Explorer module (future). This preserves the snapshot consistency rule (ARCHITECTURE.md Rule 3).

- **Real-Time = accelerated polling v1.** The real_time sync mode exists in the domain model but maps to fast-interval batch polling (e.g., 30-second pulls) using the same sync reader infrastructure. True CDC (Kafka, Debezium) is a future infrastructure swap that does not require a schema migration or domain model change.

- **Same refresh job, smarter sync reader.** The global refresh job still triggers periodically. During the source sync phase, each dataset's reader inspects its sync mode and batch_strategy: full snapshot runs SELECT *, incremental cursor runs SELECT * WHERE cursor_col > last_cursor, Direct View is skipped. No per-dataset scheduling infrastructure in v1; the frequency field is stored but not yet honored independently.

- **Cursor column auto-detection.** The system queries INFORMATION_SCHEMA.COLUMNS and matches column names against a priority list (updated_at, last_modified_at, modified_at, synced_at, last_updated, timestamp, created_at). The highest-priority timestamp column is pre-selected. Users can override via dropdown. If auto-detection finds nothing, a warning appears and the user must pick manually.

### Domain Model Changes

Dataset aggregate gains four new fields:

- sync_mode: string or null (default null, implies batch). Values: "batch", "real_time", "direct_query".
- batch_strategy: string or null. Values: "full_snapshot", "incremental_cursor". Only meaningful when sync_mode is batch.
- cursor_column: string or null. The source table column name used for incremental cursor.
- last_cursor_value: string or null. The max cursor value from the last successful pull.

New enums: SyncMode (BATCH, REAL_TIME, DIRECT_QUERY) and BatchStrategy (FULL_SNAPSHOT, INCREMENTAL_CURSOR).

Connection aggregate gains two new fields:

- test_status: string or null. Values: "untested", "success", "failed".
- last_tested_at: datetime or null. When the connection was last tested.

### API Contracts

New endpoints:

- POST /api/connections/{id}/test — Test external DB credentials. Returns success: bool and message: str.
- GET /api/connections/{id}/discover — Discover tables from external DB. Returns array of {table_name, row_count_estimate, columns: [{name, data_type}]}.
- GET /api/connections/{id}/discover/{table} — Preview a single table. Returns sample rows (10) plus full column schema.
- PATCH /api/datasets/{id}/sync-policy — Update sync mode, batch strategy, cursor column, frequency. Body accepts sync_mode, batch_strategy, cursor_column, frequency_minutes (all optional).

Modified endpoint responses:

- GET /api/datasets/{id} now includes sync_mode, batch_strategy, cursor_column, last_cursor_value, frequency_minutes.
- POST /api/datasets/ now accepts optional sync_mode, batch_strategy, cursor_column at creation time.

### Frontend Routes

New routes under /dashboard/data-studio/:

- /connections — Connection list page. Fetches and displays all connections with status badges. Has a "+ New Connection" button that opens the wizard.
- /connections/new — Connection Wizard (3-step). Step 1: source type + credentials + test. Step 2: table discovery + selection. Step 3: per-table sync policy configuration.
- /connections/[id] — Connection detail page. Shows child datasets with sync mode badges, last sync time, row count. Has "Edit sync policy" per dataset.
- /connections/[id]/datasets/[did] — Dataset detail page. Version history, preview rows, health status, re-import button.

Modified sidebar: analytics-sidebar.tsx gains a "Data Studio" entry in the ITEMS array, with child links for Connections and Datasets.

### Modules to Build or Modify

Backend new modules:

- SyncMode / BatchStrategy enums: New StrEnum classes in dataset domain.
- cursor_detection service (deep): Pure function that takes a column list and returns the best cursor column candidate.
- SecretStore interface + AES implementation (deep): Encrypt/decrypt protocol with environment-keyed AES-256-GCM implementation.
- db_source_adapter (deep): Connect/test/list/discover/sample for external Postgres and MySQL databases.
- connection_test endpoint: POST /api/connections/{id}/test route handler.
- table_discovery endpoint: GET /api/connections/{id}/discover route handler.
- sync_policy endpoint: PATCH /api/datasets/{id}/sync-policy route handler.

Backend modified modules:

- Dataset domain, schema, repository, and service: Add sync fields; DatasetService gains update_sync_policy method.
- Connection domain and schema: Add test_status and last_tested_at fields.
- source_type seed data: Enable postgresql and mysql entries.
- sync/readers: New ExternalDbReader subclass supporting full snapshot and incremental cursor queries.
- sync/orchestrator: Per-dataset awareness; iterate datasets, instantiate correct reader per sync_mode.
- Alembic migration: Add new columns to datasets and connections tables.

Frontend new modules:

- ConnectionWizard component (deep): 3-step state machine (authenticate, select objects, configure sync). Testable per-step with mocked hooks.
- SyncPolicyEditor component (deep): Per-table sync mode selector with radio toggle, strategy dropdown, frequency picker, cursor column dropdown with auto-detected badge. Pure presentational.
- Data Studio page tree: Four new pages under /dashboard/data-studio/.
- useConnectionTest hook: Calls test endpoint, returns {testing, result, error}.
- useTableDiscovery hook: Calls discover endpoint, returns {tables, loading, error}.
- Data Studio API client functions: fetchConnectionTest, fetchTableDiscovery, fetchTablePreview, updateSyncPolicy.

## Testing Decisions

### What makes a good test

Tests should verify external behavior (inputs produce correct outputs, side effects happen as specified) without depending on internal implementation details. Prefer pure functions tested with simple fixture data over framework-booted integration tests for business logic. Follow the test seam order from ARCHITECTURE.md: pure function tests first, then service tests with mocked repositories, then repository tests, then route tests, then end-to-end smoke tests.

### Which modules will be tested

Deep modules (unit tests):

- cursor_detection service: Test with various column lists (matching priorities, no matches, multiple candidates, mixed data types). Verify auto-detected returns the highest-priority timestamp column or null when nothing matches.
- SecretStore: Test encrypt/decrypt round-trip with known plaintext. Test that different keys produce different ciphertext. Test that wrong key produces decryption failure with clear error.
- db_source_adapter: Test connect (valid and invalid credentials), test (success and failure), list_tables (with various schemas), get_schema (column types), sample_rows (returns correct limit), build_query (full snapshot vs incremental cursor SQL construction). Use a test database or mock connection.
- ConnectionWizard: Test each step independently. Step 1: renders source type picker + credential form, enables Next only after test succeeds. Step 2: renders table list with checkboxes, search filter, select all, selection count. Step 3: renders SyncPolicyEditor per selected table, summary strip, Finish button disabled until all policies valid.
- SyncPolicyEditor: Test that radio toggle changes sync mode, that batch strategy and frequency appear only when Batch selected, that cursor column dropdown shows auto-detected badge when applicable, that warning appears when no column detected, that callbacks fire on each change.

Shallow modules (integration tests):

- Connection test endpoint: POST with valid credentials returns success, with invalid returns failure. Credentials encrypted in stored Connection record.
- Table discovery endpoint: GET returns table list with schemas for a test database.
- Sync policy endpoint: PATCH updates sync fields, subsequent GET reflects changes.
- Data Studio page tree: Each page renders with mocked API responses. Wizard flow completes end-to-end with mocked endpoints.

### Prior art for tests

Existing backend unit tests in tests/unit/ (e.g., test_dataset_versioning.py, test_source_type.py) use pytest with fixtures and in-memory repositories. Existing frontend unit tests in src/tests/unit/ (e.g., analytics-shell.test.tsx) use vitest with mocked hooks and next/navigation. Follow these patterns for new tests.

## Out of Scope

- True CDC infrastructure (Kafka, Debezium, WAL reading). The real_time sync mode is implemented as accelerated polling in this PRD. CDC is deferred to a future infrastructure project.
- Live Explorer module for Direct Query datasets. The sync mode is stored and respected (Direct Query datasets are skipped by the refresh pipeline), but the live query UI is a separate PRD.
- Per-dataset independent scheduling. The frequency field is stored but not yet honored independently. All Batch datasets refresh on the same global schedule for now.
- Multi-source import beyond database types (APIs, cloud storage, streaming sources). Only PostgreSQL and MySQL database connections are in scope.
- Connection health monitoring and alerting. Stretch goal for a future PRD.
- Data Freshness Widget on dashboard cards. Stretch goal; basic last-refresh timestamp is acceptable.
- Row-level access control on datasets or connections.
- Oracle database support. PostgreSQL and MySQL only for the initial implementation; the adapter interface is designed to accept additional implementations.

## Further Notes

- The connection wizard follows the Cal.com design system documented in DESIGN.md: white canvas, surface-card cards for steps, button-primary for primary actions, Inter font for all wizard UI, rounded-lg card corners.
- The source_type seed data already has postgresql and mysql entries (currently disabled). Enabling them and adding connection test/discover endpoints makes them functional.
- Existing connection lifecycle operations (pause, archive, restore, soft-delete, permanent-delete) continue to work unchanged; sync mode is orthogonal to lifecycle state.
- This PRD is the output of a grill-with-docs session. All architectural decisions are documented in ADR-0001 (per-dataset sync mode) and ADR-0002 (SecretStore encryption). Domain vocabulary is captured in CONTEXT.md.
