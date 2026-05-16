# Dashboard V2 Module Tasks

## Goal

Rebuild the dashboard as a tighter above-the-fold command view with attention
panel, 2x2 summary grid, AI summary, read-only trend chart, and top-5
department preview.

## Tasks

- [ ] Create dashboard page container that reads one active time range.
- [ ] Create 2x2 summary-card grid with `Total Spend`, `Payroll Spend`, `Claims Spend`, and `Attention Count`.
- [ ] Keep only `Attention Count` clickable in v2.
- [ ] Create dominant `Top Attention Items` panel with top 3 prioritized items.
- [ ] Add compact anomaly item layout with severity, one-line reason, and change-percent chip.
- [ ] Add `View all anomalies` CTA.
- [ ] Create supporting AI summary panel using headline plus bullets format.
- [ ] Create supporting read-only trend panel for `Total`, `Payroll`, and `Claims`.
- [ ] Create top-5 department preview list with `View all departments` CTA.
- [ ] Route department preview row click directly to department detail.
- [ ] Align component spacing, card treatment, and hierarchy with `DESIGN.md`.

## Testing

- [ ] Add unit tests for dashboard command-view mapper.
- [ ] Add unit tests for summary-card display and delta rendering.
- [ ] Add unit tests for attention-panel item rendering.
- [ ] Add integration test for `Attention Count` click carrying time range into `Anomalies`.
- [ ] Add integration test for top attention item drill-down into department detail.
