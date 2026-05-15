# Ontology Mapping Module Tasks

## Goal

Deliver snapshot-scoped ontology objects with per-entity mappers, source
lineage, and explicit attribution handling for payroll and claims.

## Tasks

- [ ] Define ontology domain types for department, employee, cost center, budget code, expense claim, and payroll expense.
- [ ] Define mapper contracts for each source entity family.
- [ ] Implement department mapper.
- [ ] Implement employee identity mapper.
- [ ] Implement cost center mapper.
- [ ] Implement budget code mapper.
- [ ] Implement claim mapper.
- [ ] Implement payroll mapper.
- [ ] Implement attribution resolver for department assignment fallback order.
- [ ] Implement ontology persistence repositories.
- [ ] Persist source lineage keys on ontology rows.
- [ ] Persist unresolved mapping or attribution failures for review instead of silently dropping them.
- [ ] Exclude unresolved records from executive aggregates until they are attributable.

## Testing

- [ ] Add backend unit tests for each mapper with exact normalized output fixtures.
- [ ] Add backend unit tests for employee identity resolution edge cases.
- [ ] Add backend unit tests for department attribution fallback order.
- [ ] Add backend integration tests for ontology persistence by snapshot.
