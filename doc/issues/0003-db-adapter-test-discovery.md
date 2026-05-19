# Issue 3: Database Source Adapter + Connection Test + Table Discovery

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

DatabaseAdapter interface with PostgreSQL implementation (asyncpg). Three new endpoints: POST /api/connections/{id}/test (validate credentials), GET /api/connections/{id}/discover (list tables with column schemas and row estimates), GET /api/connections/{id}/discover/{table} (sample rows + cursor detection). Includes cursor_detection pure function service.

## Acceptance Criteria

- [ ] DatabaseAdapter abstract interface: connect, test, list_tables, get_schema, sample_rows
- [ ] PostgreSQL implementation using asyncpg
- [ ] POST /api/connections/{id}/test returns {success: bool, message: str}
- [ ] GET /api/connections/{id}/discover returns [{table_name, row_count_estimate, columns}]
- [ ] GET /api/connections/{id}/discover/{table} returns sample rows (10) + columns
- [ ] cursor_detection service: auto-detect best cursor column from column list
- [ ] cursor_detection priority list: updated_at, last_modified_at, modified_at, synced_at, last_updated, timestamp, created_at
- [ ] Unit tests for cursor_detection (various column lists)

## Blocked by

- Issue 1 (domain foundation for Connection fields)
- Issue 2 (SecretStore for credential decryption)
