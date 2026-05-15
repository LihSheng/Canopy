# Analytics Aggregation Module Tasks

## Goal

Deliver modular monthly spend aggregates and dashboard read models that merge
validated payroll and claims data without collapsing their distinct semantics.

## Tasks

- [ ] Define aggregate domain types for monthly department spend, monthly employee spend, claim type spend, and dashboard summary cache records.
- [ ] Implement payroll monthly aggregation function.
- [ ] Implement claims monthly aggregation function.
- [ ] Implement department total merge function for payroll and claims outputs.
- [ ] Implement employee total merge function for payroll and claims outputs.
- [ ] Implement claim type contribution aggregation.
- [ ] Implement month-over-month delta calculation function.
- [ ] Implement department ranking calculation function.
- [ ] Implement dashboard summary cache builder.
- [ ] Persist analytics read models by snapshot.
- [ ] Add query helpers for dashboard summary, trend, and drill-down reads.

## Testing

- [ ] Add backend unit tests for payroll monthly aggregation.
- [ ] Add backend unit tests for claims monthly aggregation.
- [ ] Add backend unit tests for merge, ranking, and delta functions with small table-driven fixtures.
- [ ] Add backend integration tests for analytics persistence and dashboard read-model queries.
