# V5 Detailed Design: Multi-Tenant Platform and Database Architecture

## Purpose

This document defines the implementation-ready shape for v5.

V5 introduces the control-plane and tenant-data split, tenant-aware routing,
database-enforced isolation, and the operational flows needed to run the
platform safely across tenants.

## Core domain model

### User

Fields:

- `id`
- `email`
- `name`
- `password_hash`
- `status`
- `created_at`
- `updated_at`

Users are global identities in the control plane.

### Tenant

Fields:

- `id`
- `tenant_uuid`
- `name`
- `slug`
- `status`
- `lifecycle_state`
- `created_at`
- `updated_at`

The tenant UUID is the routing anchor for all tenant-owned data.

### TenantMembership

Fields:

- `id`
- `user_id`
- `tenant_id`
- `role`
- `status`
- `created_at`
- `updated_at`

Roles:

- `owner`
- `admin`
- `member`

### TenantConfig

Fields:

- `id`
- `tenant_id`
- `config_key`
- `config_value_json`
- `version_number`
- `status`
- `created_at`
- `updated_at`

Examples:

- storage limits
- queue limits
- retention policy
- feature flags

### TenantDatabaseTarget

Fields:

- `id`
- `tenant_id`
- `database_kind`
- `connection_ref`
- `status`
- `created_at`
- `updated_at`

The actual credentials live in a secret manager or encrypted secret store.

### ProvisioningJob

Fields:

- `id`
- `tenant_id`
- `job_type`
- `status`
- `started_at`
- `finished_at`
- `error_message`
- `attempt_count`

### AuditEvent

Fields:

- `id`
- `tenant_id`
- `actor_user_id`
- `event_type`
- `event_payload_json`
- `created_at`

### ImpersonationSession

Fields:

- `id`
- `platform_admin_user_id`
- `tenant_id`
- `reason`
- `started_at`
- `finished_at`
- `status`

### BackupRun

Fields:

- `id`
- `tenant_id`
- `backup_type`
- `status`
- `started_at`
- `finished_at`
- `snapshot_ref`

### RestoreRun

Fields:

- `id`
- `tenant_id`
- `source_backup_run_id`
- `status`
- `started_at`
- `finished_at`
- `error_message`

## Control plane schema

Recommended schemas:

- `auth`
- `tenants`
- `jobs`
- `audit`
- `config`

### `auth.users`

Store global identities here.

### `tenants.tenants`

Store tenant registry and lifecycle state here.

### `tenants.tenant_memberships`

Store user-to-tenant membership here.

### `tenants.tenant_configs`

Store versioned tenant config here.

### `tenants.tenant_database_targets`

Store the routing reference for each tenant here.

### `jobs.provisioning_jobs`

Track tenant setup jobs here.

### `jobs.backup_runs`

Track backup jobs here.

### `jobs.restore_runs`

Track restore jobs here.

### `audit.audit_events`

Store all platform admin and tenant lifecycle audit events here.

### `audit.impersonation_sessions`

Store support impersonation history here.

## Tenant data schema

Recommended schemas:

- `raw`
- `staging`
- `clean`
- `metadata`

### `raw.upload_batches`

Fields:

- `id`
- `tenant_id`
- `upload_name`
- `storage_key`
- `checksum`
- `size_bytes`
- `status`
- `created_at`

### `raw.raw_artifacts`

Stores immutable source file references and raw imports.

### `staging.normalized_rows`

Stores parsed and partially normalized rows.

### `clean.cleaned_records`

Stores cleaned and typed records ready for downstream query use.

### `clean.derived_read_models`

Stores persisted dashboard and API read models.

### `metadata.lineage_nodes`

Stores lineage graph nodes.

### `metadata.lineage_edges`

Stores lineage graph edges.

### `metadata.publish_states`

Stores active publish state per binding.

### `metadata.storage_objects`

Stores object metadata such as path, checksum, MIME type, and retention state.

### `metadata.job_runs`

Stores tenant refresh and processing job history.

## Tenant context and routing

### Context model

Each authenticated request resolves a dedicated `tenant_context`.

Fields:

- `tenant_id`
- `tenant_role`
- `membership_status`
- `is_impersonated`
- `database_target_ref`
- `active_token_id`

### Routing rules

- authenticate first
- revalidate membership against the control plane
- resolve tenant database target
- open a transaction on the tenant database
- call `SET LOCAL app.current_tenant_id = '...'`
- run all tenant-owned queries inside that transaction

### Implementation note

Use request-scoped context rather than thread-local state.

In the Python async backend, `contextvars.ContextVar` is the correct fit.

## Control flow

### Login and tenant switch

1. User logs in with global credentials.
2. Backend loads allowed tenants from the control plane.
3. UI presents the tenant switcher.
4. User chooses the active tenant.
5. Backend validates the membership and role.
6. Backend re-issues the JWT with the selected tenant.
7. Subsequent requests use the new tenant context.

### Tenant request execution

1. API dependency resolves the token and tenant context.
2. Membership is revalidated if required by the route.
3. Storage router resolves the tenant target.
4. Transaction opens on the tenant database.
5. `SET LOCAL app.current_tenant_id` is injected.
6. Tenant-owned repositories execute.
7. Transaction commits or rolls back.

### Provisioning

1. Platform admin creates the tenant record.
2. Tenant enters `pending` state.
3. Provisioning job creates database targets, schemas, and defaults.
4. Routing metadata is stored in the control plane.
5. Cache is invalidated.
6. Tenant becomes `active` only after validation passes.

### Cloning

1. Admin requests tenant clone.
2. Control plane validates lifecycle and retention rules.
3. Clone job creates a copy of the tenant database.
4. New routing metadata is registered.
5. Audit event records the operation.

### Backup and restore

1. Backup or restore is requested.
2. Control plane validates tenant state.
3. Job runs with tenant scope and PITR semantics.
4. Control plane records the run result.
5. Cache and routing metadata refresh.

## API design

### Suggested route groups

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `POST /api/auth/switch-tenant`
- `GET /api/tenants`
- `GET /api/tenants/{id}`
- `POST /api/admin/tenants`
- `POST /api/admin/tenants/{id}/provision`
- `POST /api/admin/tenants/{id}/impersonate`
- `POST /api/admin/tenants/{id}/suspend`
- `POST /api/admin/tenants/{id}/restore`
- `POST /api/admin/tenants/{id}/clone`
- `GET /api/admin/audit-events`
- `GET /api/admin/jobs`
- `GET /api/admin/tenant-config`

### Contract rules

- request DTOs are typed
- response payloads are typed read models
- auth routes return the active tenant context
- admin routes return job states and audit references

## Persistence decisions

### Control plane

- global users are stored only once
- tenant membership is versioned and auditable
- tenant lifecycle state is explicit
- routing metadata is separated from credentials

### Tenant data

- tenant-owned tables keep `tenant_id`
- RLS is enabled and forced
- `SET LOCAL` always happens inside a transaction
- raw data is immutable
- derived read models are persisted, not computed on every request

### Object storage

- one bucket per environment
- prefix format: `tenants/{tenant_id}/{data_category}/...`
- storage adapter stores keys, checksums, sizes, and lifecycle state

### Cache

- routing metadata uses a shared cache
- cache has a short TTL
- tenant lifecycle and provisioning events invalidate cache entries
- read models are not stored in the routing cache

## Error handling

### Membership errors

Examples:

- user is not a member of the selected tenant
- tenant is suspended
- impersonation is not allowed for the current role

Behavior:

- deny access before tenant data queries run
- return a stable authorization error
- emit an audit event for sensitive operations

### Routing errors

Examples:

- missing tenant database target
- stale cache entry
- secret lookup failure

Behavior:

- fail closed
- do not fall back to a guessed database
- mark provisioning or routing metadata as unhealthy

### RLS errors

Examples:

- missing `SET LOCAL app.current_tenant_id`
- wrong tenant context
- attempt to bypass tenant scope

Behavior:

- reject the transaction
- record the failure for observability
- do not retry blindly

### Provisioning and restore errors

Examples:

- schema migration failure
- storage prefix creation failure
- backup restore failure

Behavior:

- keep the tenant in a non-active state
- preserve previous routing metadata
- allow retry after operator review

## Test strategy

### Unit tests

Cover:

- tenant context creation
- membership validation
- tenant switch token re-issue
- database target resolution
- storage key generation
- config versioning
- job state transitions
- audit event creation

### Integration tests

Cover:

- login and tenant switch flow
- tenant-scoped request routing
- RLS isolation checks
- tenant provisioning flow
- impersonation audit flow
- backup and restore flow
- tenant cloning flow
- cache invalidation behavior

### Security tests

Cover:

- cross-tenant access blocked by RLS
- restricted role cannot bypass policies
- impersonation requires explicit audit trail
- stale membership access is denied

## Implementation risks

### Cross-tenant leakage

Risk:

- app code forgets to scope tenant requests

Mitigation:

- RLS enforced in Postgres
- transaction-scoped `SET LOCAL`
- restricted application role

### Noisy neighbor pressure

Risk:

- one tenant starves others with heavy jobs

Mitigation:

- hard quotas for safety-critical limits
- tenant-aware queues
- job fairness controls

### Migration drift

Risk:

- tenant databases diverge in schema version

Mitigation:

- shared migration pipeline
- expand-and-contract changes
- compatibility checks before cutover

### Routing inconsistency

Risk:

- cache points to the wrong database after provisioning or suspension

Mitigation:

- short TTL
- explicit invalidation
- fail-closed routing

## Deferred items

- ontology-specific data modeling
- cross-tenant business reporting
- separate cluster per tenant
- read replicas as default
- per-tenant schema drift

