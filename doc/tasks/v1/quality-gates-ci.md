# Quality Gates And CI Module Tasks

## Goal

Deliver automated quality gates that enforce modularity, FE/BE correctness, and
regression protection for analytics-heavy behavior.

## Tasks

- [ ] Define CI stages for frontend lint, frontend typecheck, frontend unit tests, and frontend integration tests.
- [ ] Define CI stages for backend lint/format validation, backend unit tests, and backend integration tests.
- [ ] Add coverage reporting for analytics, anomaly, and snapshot-related modules.
- [ ] Add failure gating for API schema regressions.
- [ ] Add failure gating for core business-rule regressions.
- [ ] Add one lightweight end-to-end smoke path covering login, dashboard, drill-down, refresh request, and export request.
- [ ] Add documentation for expected local test commands per layer.
- [ ] Add guardrails or review checklist items for untestable mixed-responsibility modules.

## Testing

- [ ] Verify CI fails when frontend unit tests fail.
- [ ] Verify CI fails when backend business-rule tests fail.
- [ ] Verify CI fails when API schema validation tests fail.
- [ ] Verify CI runs the smoke path successfully on a known-good branch.
