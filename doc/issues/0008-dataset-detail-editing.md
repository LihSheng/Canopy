# Issue 8: Dataset Detail + Sync Policy Editing

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

Dataset detail page at /dashboard/data-studio/connections/[id]/datasets/[did] with version history, preview rows, health status, re-import button. Edit sync policy inline (reuses SyncPolicyEditor from Issue 7). Force full re-pull on cursor column change.

## Acceptance Criteria

- [ ] Dataset detail page shows version history (timestamps, row counts, status)
- [ ] Dataset detail page shows preview rows
- [ ] Dataset detail page shows health status
- [ ] Re-import button triggers manual refresh
- [ ] Edit sync policy inline using SyncPolicyEditor
- [ ] Force full re-pull when cursor column changed
- [ ] User stories 23, 24, 25, 26 satisfied

## Blocked by

- Issue 4 (sync policy endpoint)
- Issue 6 (Data Studio shell)
