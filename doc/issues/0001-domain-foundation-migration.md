# Issue 1: Database Migration + Domain Foundation

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

Add SyncMode and BatchStrategy enums, new columns on `datasets` and `connections` tables, and update domain/repository/service layers. Enable `postgresql` and `mysql` source types. APIs return the new fields in responses.

## Acceptance Criteria

- [ ] `SyncMode` enum exists with values `BATCH`, `REAL_TIME`, `DIRECT_QUERY`
- [ ] `BatchStrategy` enum exists with values `FULL_SNAPSHOT`, `INCREMENTAL_CURSOR`
- [ ] `datasets` table has new columns: `sync_mode`, `batch_strategy`, `cursor_column`, `last_cursor_value`
- [ ] `connections` table has new columns: `test_status`, `last_tested_at`
- [ ] Dataset domain dataclass includes sync fields
- [ ] Connection domain dataclass includes test fields
- [ ] Repository save/load includes new fields
- [ ] DatasetService.create_dataset accepts optional sync mode
- [ ] POST /api/datasets/ accepts sync_mode, batch_strategy, cursor_column
- [ ] GET /api/datasets/{id} returns sync fields
- [ ] postgresql and mysql source types are enabled

## Blocked by

None - can start immediately
