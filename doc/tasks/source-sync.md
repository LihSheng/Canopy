# Source Sync Module Tasks

## Goal

Deliver read-only source extraction with per-entity readers, persisted snapshot
staging, and explicit sync failure handling.

## Tasks

- [ ] Define source snapshot domain types and shared reader contracts.
- [ ] Implement source reader for departments.
- [ ] Implement source reader for employees.
- [ ] Implement source reader for claims.
- [ ] Implement source reader for payroll.
- [ ] Implement source reader for cost centers.
- [ ] Implement source reader for budget codes.
- [ ] Implement source snapshot persistence repository.
- [ ] Implement sync orchestration that extracts each entity family into one snapshot.
- [ ] Record extraction timestamps and sync errors per snapshot.
- [ ] Ensure source access remains read-only and isolated to this module.
- [ ] Add explicit handling for empty source result sets versus hard failures.

## Testing

- [ ] Add backend unit tests for each source reader contract using fixture source rows.
- [ ] Add backend unit tests for sync orchestration success and partial-failure paths.
- [ ] Add backend integration tests for snapshot persistence and extraction metadata recording.
