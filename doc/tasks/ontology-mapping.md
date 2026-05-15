# Ontology Mapping Module Tasks

## Goal

Deliver snapshot-scoped ontology objects with per-entity mappers, source
lineage, and explicit attribution handling for payroll and claims.

## Tasks

- [x] Define ontology domain types for department, employee, cost center, budget code, expense claim, and payroll expense.
- [x] Define mapper contracts for each source entity family.
- [x] Implement department mapper.
- [x] Implement employee identity mapper.
- [x] Implement cost center mapper.
- [x] Implement budget code mapper.
- [x] Implement claim mapper.
- [x] Implement payroll mapper.
- [x] Implement attribution resolver for department assignment fallback order.
- [x] Implement ontology persistence repositories.
- [x] Persist source lineage keys on ontology rows.
- [x] Persist unresolved mapping or attribution failures for review instead of silently dropping them.
- [x] Exclude unresolved records from executive aggregates until they are attributable.

## Testing

- [x] Add backend unit tests for each mapper with exact normalized output fixtures.
- [x] Add backend unit tests for employee identity resolution edge cases.
- [x] Add backend unit tests for department attribution fallback order.
- [x] Add backend integration tests for ontology persistence by snapshot.
