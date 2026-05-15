# API Module Tasks

## Goal

Deliver thin FastAPI route groups with explicit schemas and stable transport
contracts over the backend service layer.

## Tasks

- [x] Define shared API response envelope schema.
- [x] Define transport schemas for dashboard summary payloads.
- [x] Define transport schemas for department detail and drill-down payloads.
- [x] Define transport schemas for anomaly payloads.
- [x] Define transport schemas for refresh request and refresh status payloads.
- [x] Define transport schemas for export request and export response payloads.
- [x] Create route group modules for `auth`, `dashboard`, `departments`, `anomalies`, `refresh`, and `exports`.
- [x] Implement request-to-service DTO translation helpers where needed.
- [x] Add consistent API error translation for validation and internal failures.
- [x] Ensure route handlers contain no aggregation, anomaly, or mapping logic inline.
- [x] Add route registration and dependency wiring.

## Testing

- [x] Add API schema tests for request and response payload validation.
- [x] Add route integration tests for each route group using mocked or test-backed services.
- [x] Add regression tests confirming stable error envelope shape for common failures.
