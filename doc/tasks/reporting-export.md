# Reporting And Export Module Tasks

## Goal

Deliver Excel export from snapshot-aligned read models, with formatting isolated
from data retrieval so export behavior stays testable.

## Tasks

- [x] Define export request and export payload domain types.
- [x] Implement export read-model query service using the same snapshot basis as dashboard reads.
- [x] Define workbook structure for executive summary and breakdown sheets.
- [x] Implement workbook builder.
- [x] Implement sheet-level formatting helpers isolated from data fetching.
- [x] Implement export service that composes read-model retrieval and workbook build.
- [x] Add export endpoint integration with auth protection.
- [x] Ensure export metadata reflects snapshot alignment where useful.

## Testing

- [x] Add backend unit tests for workbook builder sheet content.
- [x] Add backend unit tests for export formatting helpers.
- [x] Add backend service tests confirming export uses the same snapshot basis as dashboard reads.
- [x] Add backend integration test for export endpoint success path.
