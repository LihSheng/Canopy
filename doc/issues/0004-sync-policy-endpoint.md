# Issue 4: Sync Policy Endpoint

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

PATCH /api/datasets/{id}/sync-policy endpoint. Validates and updates sync_mode, batch_strategy, cursor_column, frequency_minutes. Cursor column change forces last_cursor_value reset to null.

## Acceptance Criteria

- [ ] PATCH /api/datasets/{id}/sync-policy accepts sync_mode, batch_strategy, cursor_column, frequency_minutes (all optional)
- [ ] Validates sync_mode against SyncMode enum
- [ ] Validates batch_strategy against BatchStrategy enum (only when sync_mode=batch)
- [ ] Changing cursor_column resets last_cursor_value to null
- [ ] GET /api/datasets/{id} returns updated sync fields
- [ ] Integration test: PATCH then verify GET reflects changes

## Blocked by

- Issue 1 (domain foundation)
