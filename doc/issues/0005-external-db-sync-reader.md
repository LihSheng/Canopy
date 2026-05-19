# Issue 5: External Database Sync Reader

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

New ExternalDbReader subclass of SourceReader. Full snapshot mode runs SELECT *. Incremental cursor mode runs SELECT * WHERE cursor_col > last_cursor_value. Direct Query datasets are skipped. Sync orchestrator iterates all datasets and picks the correct reader per sync_mode.

## Acceptance Criteria

- [ ] ExternalDbReader implements SourceReader contract
- [ ] Full snapshot strategy: reads all rows from source table
- [ ] Incremental cursor strategy: reads rows where cursor_col > last_cursor_value
- [ ] Direct Query datasets are skipped by orchestrator
- [ ] Sync orchestrator iterates datasets and picks correct reader per sync_mode
- [ ] last_cursor_value updated after successful incremental pull
- [ ] First incremental pull (null cursor) pulls everything

## Blocked by

- Issue 3 (DatabaseAdapter for external DB connection)
- Issue 4 (sync policy endpoint for field updates)
