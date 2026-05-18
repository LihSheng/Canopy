# V5 High-Level Design: Multi-Tenant Platform and Database Architecture

## Overview

V5 turns the platform into a tenant-aware system with a shared control plane
and tenant data plane.

The main shift is not a new user feature.
The main shift is a storage and routing model:

- platform metadata lives in the control plane
- tenant business data lives in tenant data storage
- the application routes every request through an explicit tenant context
- PostgreSQL RLS provides the hard isolation boundary

This design is the future multi-tenant track and is separate from ontology
modeling.

## Major modules

### 1. Identity and Tenant Access Module

Responsible for:

- login
- session issuance
- tenant membership lookup
- tenant switching
- JWT re-issue with the active tenant

### 2. Tenant Context Module

Responsible for:

- creating request-scoped tenant context
- carrying tenant ID, active role, and impersonation state
- validating tenant membership on each authenticated request

### 3. Control Plane Module

Responsible for:

- user records
- tenant registry
- membership records
- tenant lifecycle state
- tenant config and feature flags
- provisioning metadata
- audit logs
- routing metadata for tenant databases

### 4. Tenant Provisioning Module

Responsible for:

- creating tenant database records
- initializing schema bundles
- seeding defaults
- creating storage prefixes
- marking a tenant active only after setup completes

### 5. Tenant Data Routing Module

Responsible for:

- resolving the correct storage target from tenant metadata
- opening the right database connection pool
- starting a transaction with the tenant context
- injecting `SET LOCAL app.current_tenant_id`

### 6. Tenant Data Module

Responsible for:

- tenant-owned persistence
- raw, staging, clean, and metadata schemas
- RLS-enforced read and write access
- immutable snapshots and derived read models

### 7. Object Storage Module

Responsible for:

- file storage adapter
- tenant-rooted object keys
- checksums and metadata
- local-dev storage fallback

### 8. Job Orchestration Module

Responsible for:

- tenant provisioning jobs
- schema rollout jobs
- import/refresh jobs
- restore and clone jobs
- tenant-aware queue fairness

### 9. Backup and Restore Module

Responsible for:

- tenant-scoped PITR policy
- control-plane backup policy
- restore validation
- tenant cloning

### 10. Audit and Observability Module

Responsible for:

- audit event capture
- impersonation trail
- provisioning trail
- tenant lifecycle trail
- operational metrics and failure reasons

### 11. Cache and Configuration Module

Responsible for:

- routing metadata cache
- tenant config cache
- feature flag cache
- cache invalidation on provisioning and lifecycle changes

## Data flow

### Login and tenant switch flow

1. User logs in.
2. Control plane loads user membership list.
3. UI shows tenant switcher.
4. User selects an active tenant.
5. Backend re-issues the JWT with the selected tenant.
6. Tenant context is created for subsequent requests.

### Tenant request flow

1. API receives an authenticated request.
2. Backend validates the user against control-plane membership.
3. Backend resolves the tenant storage target.
4. Backend opens the tenant data transaction.
5. Backend injects `SET LOCAL app.current_tenant_id`.
6. Tenant-owned queries run through RLS.
7. Response returns only tenant-scoped data.

### Provisioning flow

1. Platform admin creates a tenant.
2. Control plane records tenant state as pending.
3. Provisioning job creates schema and storage targets.
4. Defaults and limits are seeded.
5. Routing metadata is published.
6. Tenant becomes active only after validation passes.

### Backup and restore flow

1. Admin requests backup or restore.
2. Control plane validates tenant lifecycle state.
3. Backup or restore job runs with tenant scope.
4. Job result is recorded in the control plane.
5. Cache and routing metadata are refreshed.

## External interfaces

### Frontend to backend

Main capability groups:

- auth
- tenant switching
- tenant administration
- provisioning
- backups and restore
- audit history
- tenant config

### Backend to PostgreSQL

- control plane database
- tenant data database
- transaction-scoped tenant context

### Backend to object storage

- tenant-rooted paths
- presigned URL or scoped access model

### Backend to cache

- routing metadata
- tenant config
- feature flags

## Cross-cutting concerns

### Security

- database is the isolation boundary
- app context is required but not sufficient on its own
- platform admin impersonation must be audited
- secrets live in a secret manager or encrypted secret store

### Consistency

- tenant switch re-issues the token
- cache invalidation happens on lifecycle changes
- control plane and tenant data remain separate but coordinated

### Reliability

- provisioning and restore are job-driven
- migration rollout is backward compatible
- tenant cloning is supported for support and testing

### Performance

- use a shared cache for routing metadata
- keep heavy tenant work in queues
- apply hard limits to safety-critical operations

## Main tradeoffs

- Shared storage is simpler now, but dedicated tenant databases remain the
  future extraction target.
- RLS is safer than app-only filtering, but it requires stricter transaction
  discipline.
- A shared cache improves routing and config lookup, but must be invalidated
  carefully.
- Tenant cloning is useful for support, but it increases operational surface.

## Deferred items

- ontology modeling
- cross-tenant business analytics
- read replicas as a default requirement
- per-tenant schema drift
- separate cluster per tenant

