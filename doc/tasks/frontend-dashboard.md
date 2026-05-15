# Frontend Dashboard Module Tasks

## Goal

Deliver the executive dashboard UI with modular containers, presentational
components, typed adapters, and drill-down navigation that stays easy to test.

## Tasks

- [ ] Create frontend app shell, dashboard layout, and shared page container primitives.
- [ ] Create shared loading, empty, stale, and error state components.
- [ ] Create dashboard summary card frame component.
- [ ] Create total payroll summary card.
- [ ] Create total claims summary card.
- [ ] Create top departments summary card.
- [ ] Create anomaly highlights summary card.
- [ ] Create monthly trend chart component with separate chart data mapper.
- [ ] Create department ranking chart component with separate chart data mapper.
- [ ] Create claim type breakdown chart component with separate chart data mapper.
- [ ] Create department detail page container.
- [ ] Create employee contribution table shell and column mapper.
- [ ] Create claim detail table shell and column mapper.
- [ ] Create month and filter controls with serializable route state.
- [ ] Create anomalies list page container.
- [ ] Create refresh status badge, refresh timeline panel, and manual refresh button components.
- [ ] Wire all page containers through typed API adapters only.
- [ ] Align tokens and component surfaces with `DESIGN.md`.

## Testing

- [ ] Add frontend unit tests for summary cards with plain props.
- [ ] Add frontend unit tests for chart data mapper functions.
- [ ] Add frontend unit tests for drill-down tables and empty/loading/error states.
- [ ] Add frontend unit tests for refresh widgets across queued/running/failed/completed states.
- [ ] Add frontend integration tests for dashboard load, department drill-down, anomaly navigation, and refresh UX.
