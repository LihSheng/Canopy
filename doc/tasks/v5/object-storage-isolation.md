# Object Storage Isolation

## Goal

Implement tenant-rooted object storage for uploads, raw artifacts, cleaned
artifacts, and export-ready files.

## Tasks

- [x] Add a file storage adapter with local-dev and production backends.
- [x] Use one bucket per environment.
- [x] Prefix every tenant file path with `tenants/{tenant_id}/...`.
- [x] Persist object key, checksum, size, MIME type, and lifecycle state.
- [x] Store raw and cleaned artifacts as immutable objects.
- [x] Add access-scope checks for tenant-scoped file retrieval.
- [x] Add lifecycle-aware cleanup and retention handling for stored objects.

## Testing

- [x] Add unit tests for storage key generation and metadata persistence.
- [x] Add integration tests for tenant-isolated upload and download behavior.
- [x] Add regression tests that prevent cross-tenant file access.

