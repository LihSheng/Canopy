# Source Sync Module Tasks

## Goal

Deliver read-only source extraction with per-entity readers, persisted snapshot
staging, and explicit sync failure handling.

## Tasks

- [x] Define source snapshot domain types and shared reader contracts.
- [x] Implement source reader for departments.
- [x] Implement source reader for employees.
- [x] Implement source reader for claims.
- [x] Implement source reader for payroll.
- [x] Implement source reader for cost centers.
- [x] Implement source reader for budget codes.
- [x] Implement source snapshot persistence repository.
- [x] Implement sync orchestration that extracts each entity family into one snapshot.
- [x] Record extraction timestamps and sync errors per snapshot.
- [x] Ensure source access remains read-only and isolated to this module.
- [x] Add explicit handling for empty source result sets versus hard failures.

## Testing

- [x] Add backend unit tests for each source reader contract using fixture source rows.
- [x] Add backend unit tests for sync orchestration success and partial-failure paths.
- [x] Add backend integration tests for snapshot persistence and extraction metadata recording.
