# V5 Database Architecture

## Purpose

This document defines the platform database foundation for the future multi-
tenant phase.

Note:

- `v5` is a planning label for this document set only
- implementation names must use domain terms, not phase prefixes
- tables, schemas, files, routes, and jobs should not be named `v5_*` or
  `v3_*`

It stays aligned with [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/Canopy/ARCHITECTURE.md)
and the v5 planning docs. If it conflicts with `ARCHITECTURE.md`, the system
source of truth wins.

## Decisions locked for v5

- one PostgreSQL cluster
- one shared tenant data database for the current stage
- one separate control-plane database in the same cluster
- tenant isolation enforced by application context plus PostgreSQL RLS
- `tenant_id` is always a UUID
- UUIDv4 is the default ID format for system entities
- object storage is the file layer, with one bucket per environment
- tenant storage paths use `tenants/{tenant_id}/...`
- future move to dedicated per-tenant databases remains supported

## Database roles

### 1. Control plane database

The control plane stores platform-owned records that are not tenant business
data.

Responsibilities:

- user accounts
- tenant registry
- tenant membership records
- platform admin records
- authentication and session metadata
- tenant lifecycle state
- provisioning jobs
- migration orchestration metadata
- tenant config and feature flags
- audit logs

Rules:

- no tenant business facts live here
- tenant actions are auditable
- tenant lifecycle changes are explicit and versioned
- credentials for downstream tenant databases are not stored in plain text

### 2. Shared tenant data database

The tenant data database stores tenant-owned business data for the current
stage.

Responsibilities:

- uploaded file metadata
- raw workbook snapshots
- staging data
- cleaned data
- lineage data
- publish state
- refresh job history
- derived read models

Rules:

- every tenant-owned table includes `tenant_id UUID NOT NULL`
- PostgreSQL RLS is enabled on every tenant-owned table
- application queries run with a transaction-scoped tenant context
- application code must not rely on manually adding `WHERE tenant_id = ...`
- the database must reject cross-tenant access even if application code fails

## Physical layout

### Cluster

Use a single PostgreSQL cluster for the current platform stage.

The cluster contains:

- `control_plane`
- `tenant_data`

This keeps the operational footprint small while preserving the control-plane
and data-plane boundary.

### Tenant database future path

The shared tenant data database is the current default.

If a tenant needs dedicated isolation later, the same schema bundle can be
provisioned into a separate database in the same cluster or into a different
cluster. The application should route by tenant metadata, not by hardcoded
connection assumptions.

## Schema layout

### Control plane schemas

Recommended schemas:

- `auth`
- `tenants`
- `jobs`
- `audit`
- `config`

### Tenant data schemas

Recommended schemas:

- `raw`
- `staging`
- `clean`
- `metadata`

Notes:

- raw and staged imports stay separate from cleaned records
- metadata holds mappings, lineage, and publish-related control tables
- one schema bundle should be reused across all tenant databases

## Tenant context

Each authenticated request resolves to a dedicated `tenant_context`.

That context contains:

- `tenant_id`
- tenant role
- membership state
- impersonation state
- database routing target

Rules:

- context is request-scoped
- the active tenant is revalidated against control-plane membership
- tenant switching re-issues the JWT
- the app uses the context to select the correct storage target

## Security model

### Authentication and membership

- global users live in the control plane
- tenant membership lives in the control plane
- a user can belong to multiple tenants
- tenant switching happens after login through the UI

### Database isolation

- tenant-owned tables use RLS
- the application sets `SET LOCAL app.current_tenant_id = '...'` inside an
  explicit transaction
- the application role is restricted and not a superuser
- `FORCE ROW LEVEL SECURITY` is enabled on tenant-owned tables

### Admin access

- platform admins exist separately from tenant users
- platform admins can impersonate a tenant context
- every impersonation action is audited

## Storage model

### Object storage

All uploaded files and file-derived artifacts use object storage.

Rules:

- one bucket per environment
- tenant prefixes inside the bucket
- path shape: `tenants/{tenant_id}/{data_category}/...`
- file storage is an adapter, not a business logic concern
- local file storage is acceptable for development only

### Stored metadata

The database stores:

- object key
- checksum
- size
- MIME type
- tenant ownership
- lifecycle state
- retention state

## IDs

Use UUIDv4 for system identifiers unless a later implementation decision
requires a different format for a specific hot path.

Rules:

- no sequential integer IDs for multi-tenant business entities
- `tenant_id` is always UUID
- IDs must remain portable if a tenant is later moved to its own database

## Config and lifecycle

### Tenant config

Tenant config is stored in the control plane and versioned.

Examples:

- storage limits
- queue limits
- retention policy
- feature flags

### Lifecycle states

Tenant lifecycle should be explicit.

Suggested states:

- `pending`
- `active`
- `suspended`
- `archived`
- `deleted`

Rules:

- archived tenants remain restorable
- hard delete happens only after retention expiry and explicit admin action

## Jobs

Split job ownership by plane.

### Control plane jobs

- tenant provisioning
- tenant database creation
- schema rollout
- tenant suspension
- tenant restore

### Tenant data jobs

- workbook ingest
- profiling
- mapping
- cleaning
- normalization
- lineage generation
- publish activation
- refresh runs

Rules:

- jobs are tenant-aware
- quotas apply from day one
- safety-critical limits are hard enforced
- growth limits can warn first

## Migration strategy

### Current rule

Use expand-and-contract migrations.

### Rollout rule

- migrations run through a shared pipeline
- all tenant databases stay on the same schema version
- schema changes must stay backward compatible during rollout
- DDL should avoid blocking operations where possible

### Future extraction rule

The shared schema bundle must remain portable so a tenant can be moved into a
dedicated database later without changing business logic.

## Backups and restore

Separate backup and retention policy by plane.

### Control plane

- backup independently from tenant data
- restore independently from tenant data

### Tenant data

- tenant-scoped backup and restore
- automated backups with PITR
- tenant cloning supported for support and testing

## Caching

Use shared cache for routing and tenant config metadata.

Rules:

- cache is required in production
- in-memory fallback is for local development only
- invalidate cache on tenant provisioning, suspension, config change, or DB
  rotation
- do not cache dashboard read models in the routing cache

## Deferred items

Ontology-specific database modeling is intentionally out of scope for v5
database architecture and will be documented separately.
