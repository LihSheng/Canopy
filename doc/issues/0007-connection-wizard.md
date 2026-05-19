# Issue 7: Connection Wizard (Full 3-Step Flow)

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

ConnectionWizard component at /dashboard/data-studio/connections/new. Step 1: source type picker + credential form + "Test Connection" button. Step 2: table list with checkboxes, search, select all, selection count. Step 3: SyncPolicyEditor per selected table with sync mode radio toggle, strategy dropdown, frequency picker, cursor column dropdown with auto-detected badge.

## Acceptance Criteria

- [ ] Step 1: source type dropdown + credential form + Test Connection button
- [ ] Next button disabled until test succeeds
- [ ] Step 2: table list with checkboxes, search filter, select all toggle
- [ ] Running selection count displayed
- [ ] Step 3: SyncPolicyEditor renders per selected table
- [ ] Radio toggle switches sync mode (Batch, Real-Time, Direct View)
- [ ] Batch strategy dropdown appears only when Batch selected
- [ ] Frequency picker appears only when Batch selected
- [ ] Cursor column dropdown shows auto-detected column with badge
- [ ] Warning when no cursor column auto-detected
- [ ] Summary strip shows "N tables configured"
- [ ] "Finish & Deploy" creates connection + datasets with sync policies
- [ ] Unit tests for ConnectionWizard (each step independently)

## Blocked by

- Issue 6 (Data Studio shell)
