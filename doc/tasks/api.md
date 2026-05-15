# API Module Tasks

## Goal

Deliver thin FastAPI route groups with explicit schemas and stable transport
contracts over the backend service layer.

## Tasks

- [ ] Define shared API response envelope schema.
- [ ] Define transport schemas for dashboard summary payloads.
- [ ] Define transport schemas for department detail and drill-down payloads.
- [ ] Define transport schemas for anomaly payloads.
- [ ] Define transport schemas for refresh request and refresh status payloads.
- [ ] Define transport schemas for export request and export response payloads.
- [ ] Create route group modules for `auth`, `dashboard`, `departments`, `anomalies`, `refresh`, and `exports`.
- [ ] Implement request-to-service DTO translation helpers where needed.
- [ ] Add consistent API error translation for validation and internal failures.
- [ ] Ensure route handlers contain no aggregation, anomaly, or mapping logic inline.
- [ ] Add route registration and dependency wiring.

## Testing

- [ ] Add API schema tests for request and response payload validation.
- [ ] Add route integration tests for each route group using mocked or test-backed services.
- [ ] Add regression tests confirming stable error envelope shape for common failures.
