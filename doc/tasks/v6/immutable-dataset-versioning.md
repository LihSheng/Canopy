# Immutable Dataset Versioning

## Goal

Create a new dataset version for every re-import and keep previous versions inspectable.

## Tasks

- [ ] Define the dataset version state and storage fields.
- [ ] Create a new version on each successful import.
- [ ] Track row count, column count, and storage path per version.
- [ ] Mark the active version on the dataset record.
- [ ] Keep older versions available for inspection.

## Testing

- [ ] Verify version number increments on re-import.
- [ ] Verify a failed import does not activate a new version.
- [ ] Verify prior versions remain listed.

