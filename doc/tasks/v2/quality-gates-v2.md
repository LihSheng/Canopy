# Quality Gates V2 Module Tasks

## Goal

Protect the v2 shell and page refresh with focused FE and BE verification so
navigation, route-state carry-over, and read-model shaping do not regress.

## Tasks

- [ ] Add frontend test coverage for shell, route-state, and v2 page mappers.
- [ ] Add frontend integration coverage for dashboard, anomalies, departments, department detail, reports, and profile navigation.
- [ ] Add responsive behavior checks for drawer-mode navigation.
- [ ] Add backend tests for new or revised v2 read-model assemblers.
- [ ] Add backend route tests for v2-specific contract changes.
- [ ] Keep CI gating strict on route-state and read-model regressions.

## Testing

- [ ] Verify no v2 page depends on raw JSON parsing inside components.
- [ ] Verify route-state carry-over coverage exists for dashboard-to-anomalies and department-detail-to-anomalies flows.
- [ ] Verify shell behavior is tested independently from page business-data loading.
