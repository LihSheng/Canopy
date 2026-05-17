# Upload Wizard And File Storage

## Goal

Accept Excel uploads from non-technical users and store the original file
immutably so profiling and preview can be replayed later.

## Tasks

- [x] Define the upload request/response contract.
- [x] Implement frontend upload wizard state and validation.
- [x] Validate file type, size, and basic workbook readability.
- [x] Persist the uploaded file to immutable storage.
- [x] Create an upload snapshot record with checksum and metadata.
- [ ] Trigger profiling after successful storage.
- [x] Preserve failed uploads for retry and inspection.

## Testing

- [x] Add backend tests for file validation and snapshot creation.
- [x] Add backend tests for immutable storage path handling.
- [x] Add frontend tests for upload-state transitions and validation errors.

