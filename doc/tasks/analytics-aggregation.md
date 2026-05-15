# Analytics Aggregation Module Tasks

## Goal

Deliver modular monthly spend aggregates and dashboard read models that merge
validated payroll and claims data without collapsing their distinct semantics.

## Tasks

- [x] Define aggregate domain types for monthly department spend, monthly employee spend, claim type spend, and dashboard summary cache records.
- [x] Implement payroll monthly aggregation function.
- [x] Implement claims monthly aggregation function.
- [x] Implement department total merge function for payroll and claims outputs.
- [x] Implement employee total merge function for payroll and claims outputs.
- [x] Implement claim type contribution aggregation.
- [x] Implement month-over-month delta calculation function.
- [x] Implement department ranking calculation function.
- [x] Implement dashboard summary cache builder.
- [x] Persist analytics read models by snapshot.
- [x] Add query helpers for dashboard summary, trend, and drill-down reads.

## Testing

- [x] Add backend unit tests for payroll monthly aggregation.
- [x] Add backend unit tests for claims monthly aggregation.
- [x] Add backend unit tests for merge, ranking, and delta functions with small table-driven fixtures.
- [x] Add backend integration tests for analytics persistence and dashboard read-model queries.
