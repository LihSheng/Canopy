# Issue 6: Data Studio Page Shell + Connection List

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

Add "Data Studio" to sidebar navigation. Create /dashboard/data-studio/connections page with connection list (status badges, names, source types, "+ New Connection" button). Create /dashboard/data-studio/connections/[id] page shell showing child datasets with sync mode badges.

## Acceptance Criteria

- [ ] "Data Studio" entry added to sidebar ITEMS array
- [ ] /dashboard/data-studio/connections page renders connection list from API
- [ ] Each connection card shows name, source type, status badge
- [ ] "+ New Connection" button navigates to wizard
- [ ] /dashboard/data-studio/connections/[id] page renders child datasets
- [ ] Each dataset card shows name, sync mode badge, last sync time, row count
- [ ] Follows Cal.com design tokens (herd- css variables)

## Blocked by

- Issue 3 (table discovery/connection test API)
