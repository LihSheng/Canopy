# Reporting And Export Module Tasks

## Goal

Deliver Excel export from snapshot-aligned read models, with formatting isolated
from data retrieval so export behavior stays testable.

## Tasks

- [ ] Define export request and export payload domain types.
- [ ] Implement export read-model query service using the same snapshot basis as dashboard reads.
- [ ] Define workbook structure for executive summary and breakdown sheets.
- [ ] Implement workbook builder.
- [ ] Implement sheet-level formatting helpers isolated from data fetching.
- [ ] Implement export service that composes read-model retrieval and workbook build.
- [ ] Add export endpoint integration with auth protection.
- [ ] Ensure export metadata reflects snapshot alignment where useful.

## Testing

- [ ] Add backend unit tests for workbook builder sheet content.
- [ ] Add backend unit tests for export formatting helpers.
- [ ] Add backend service tests confirming export uses the same snapshot basis as dashboard reads.
- [ ] Add backend integration test for export endpoint success path.
