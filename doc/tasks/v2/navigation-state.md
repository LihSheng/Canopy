# Navigation State Module Tasks

## Goal

Centralize time-range state, drill-down context, and URL/query construction so
page transitions stay explicit and testable.

## Tasks

- [x] Create shared `TimeRangeKey` model and default-range helper.
- [x] Create route-state parser for dashboard, anomalies, and department flows.
- [x] Create typed link builders for dashboard-to-anomalies navigation.
- [x] Create typed link builders for dashboard-to-department-detail navigation.
- [x] Create typed link builders for department-detail-to-anomalies navigation.
- [x] Keep all route-state values serializable and URL-safe.
- [x] Remove ad hoc query-string construction from page components.

## Testing

- [x] Add table-driven unit tests for time-range parsing and fallback behavior.
- [x] Add unit tests for dashboard attention-item link builders.
- [x] Add unit tests for `View related anomalies` context carry-over.
