# Issue 9: Integration Tests

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

End-to-end wizard flow test, connection test endpoint tests, table discovery tests, sync policy update tests, dashboard unchanged verification, frontend component tests for ConnectionWizard, SyncPolicyEditor, and Data Studio pages.

## Acceptance Criteria

- [ ] Wizard flow test: authenticate → select tables → configure sync → deploy → verify
- [ ] Connection test: valid and invalid credentials
- [ ] Table discovery: returns schemas for test database
- [ ] Sync policy: PATCH + verify GET reflects changes
- [ ] Dashboard unchanged: existing pages work after sync mode changes
- [ ] ConnectionWizard component tests (per-step rendering, validation)
- [ ] SyncPolicyEditor component tests (mode toggle, dropdowns, badges, callbacks)
- [ ] Data Studio page tests (list, detail, wizard)

## Blocked by

- Issues 1 through 8
