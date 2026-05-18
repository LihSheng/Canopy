# Tenant Data Routing And RLS

## Goal

Implement tenant-data routing, row-level security, schema portability, and the
shared migration pipeline for tenant-owned records.

## Tasks

- [x] Create tenant data schemas for raw, staging, clean, and metadata.
- [x] Add `tenant_id UUID NOT NULL` to every tenant-owned table.
- [x] Enable and force PostgreSQL RLS on tenant-owned tables.
- [x] Inject `SET LOCAL app.current_tenant_id` inside every tenant transaction.
- [x] Route requests to the correct tenant database target.
- [x] Keep the storage router isolated from business logic.
- [x] Implement the shared migration pipeline for tenant databases.
- [x] Apply expand-and-contract rollout rules for schema changes.
- [x] Keep schema names and table shapes portable for future tenant extraction.

## Testing

- [x] Add unit tests for routing-target resolution.
- [x] Add integration tests for tenant-scoped transactions and RLS isolation.
- [x] Add migration compatibility tests for backward-compatible rollouts.

