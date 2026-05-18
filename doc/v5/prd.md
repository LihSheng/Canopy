# V5 PRD: Multi-Tenant Platform and Database Architecture

## Problem Statement

The platform needs a clean multi-tenant foundation before it can safely scale
into a shared production system.

Today, the product needs a way to separate tenant data, control-plane data, and
tenant access decisions without relying on fragile application-only filtering.
It also needs a path that starts simple now and can later split tenants into
dedicated databases without rewriting the whole application.

The current problem is not just storage. It is the combination of:

- tenant isolation
- safe tenant switching
- provisioning and lifecycle management
- auditing
- routing to the correct database
- file isolation in object storage
- backup and restore by tenant
- protection against noisy neighbors

Without a clear platform database model, the system risks cross-tenant leakage,
hard-to-debug routing bugs, and a future migration trap.

## Solution

Build a tenant-aware platform foundation with:

- one PostgreSQL cluster
- a shared control-plane database for identity, tenant registry, memberships,
  provisioning, config, audit, and routing metadata
- a shared tenant data database for the current stage
- request-scoped tenant context
- PostgreSQL row-level security on tenant-owned tables
- transaction-scoped tenant injection with `SET LOCAL app.current_tenant_id`
- one bucket per environment for object storage, with tenant-rooted prefixes
- UUIDv4-based identifiers
- tenant-scoped backups, restores, and cloning
- queued provisioning and operational jobs
- tenant-level quotas and tenant-aware queues
- a future path to move a tenant into its own database without changing
  application services

The platform should keep the control plane and tenant data plane separate in
responsibility, while keeping the codebase modular and routing-driven.

## User Stories

1. As a platform admin, I want to create a tenant from the control plane, so
   that tenant setup is repeatable and auditable.
2. As a platform admin, I want tenant provisioning to run as a background job,
   so that setup can be retried safely without freezing the UI.
3. As a platform admin, I want to see provisioning status, so that I know when
   a tenant is ready.
4. As a platform admin, I want to suspend a tenant, so that access can be
   stopped immediately when needed.
5. As a platform admin, I want to restore a suspended or archived tenant, so
   that recovery is possible without recreating the tenant.
6. As a platform admin, I want to clone a tenant into a new database, so that I
   can support future migrations and safe testing.
7. As a platform admin, I want every lifecycle action to be audited, so that
   support actions can be traced later.
8. As a platform admin, I want to manage tenant config centrally, so that
   quotas, flags, and retention rules can be changed without code deploys.
9. As a platform admin, I want to impersonate a tenant with an audit trail, so
   that I can debug support issues safely.
10. As a tenant user, I want to log in with a global identity, so that I do not
   need separate accounts for each tenant.
11. As a tenant user, I want to switch tenants after login, so that I can work
   across multiple tenant contexts.
12. As a tenant user, I want the system to re-issue my token when I switch
   tenants, so that the active tenant is explicit and trusted.
13. As a tenant user, I want only the tenants I belong to to appear in the
   switcher, so that I cannot access unauthorized data.
14. As a tenant user, I want the active tenant context to be validated on each
   request, so that stale membership cannot be used to bypass access rules.
15. As a tenant user, I want tenant data to stay isolated from other tenants,
   so that my records cannot be exposed accidentally.
16. As a tenant user, I want uploads and derived files to be stored under my
   tenant namespace, so that file access stays isolated.
17. As a tenant user, I want raw uploads to remain immutable, so that audit and
   reprocessing are possible.
18. As a tenant user, I want cleaned outputs and read models to be persisted,
   so that dashboards and exports are fast and consistent.
19. As a tenant user, I want backups and restores to be tenant-scoped, so that
   recovery does not affect unrelated tenants.
20. As a tenant user, I want storage and compute limits to be enforced fairly,
   so that one tenant cannot starve others.
21. As a tenant user, I want warning thresholds before soft limits are reached,
   so that I can avoid hitting hard caps unexpectedly.
22. As a support operator, I want tenant routing metadata to be cached, so that
   normal requests stay fast.
23. As a support operator, I want routing cache invalidation on lifecycle
   changes, so that stale database references do not linger.
24. As a developer, I want every tenant-owned table to have `tenant_id`, so
   that the schema remains portable if tenants later split into dedicated DBs.
25. As a developer, I want PostgreSQL RLS to enforce isolation, so that app
   mistakes do not become data leaks.
26. As a developer, I want tenant-scoped work to run inside explicit
   transactions, so that `SET LOCAL` always works correctly.
27. As a developer, I want a storage router boundary, so that the application
   can later point a tenant at a dedicated database without changing services.
28. As a developer, I want one schema bundle reused across tenant databases, so
   that migration behavior stays consistent.
29. As a developer, I want schema changes to roll out with expand-and-contract
   migrations, so that tenant databases remain compatible during deployment.
30. As a developer, I want object storage paths to be tenant-prefixed, so that
   storage separation is consistent across environments.

## Implementation Decisions

- Use one PostgreSQL cluster for the current platform.
- Keep a separate control-plane database and tenant data database in that
  cluster.
- Store global identities, tenant registry, memberships, lifecycle state,
  provisioning jobs, audit logs, tenant config, and routing metadata in the
  control plane.
- Store tenant-owned business data in the tenant data database.
- Keep tenant-owned tables portable by including `tenant_id UUID NOT NULL`.
- Enforce tenant isolation with PostgreSQL RLS and transaction-scoped tenant
  context.
- Re-issue the JWT when the user switches tenants.
- Allow a user to belong to multiple tenants.
- Use a simple `owner` / `admin` / `member` membership model.
- Keep platform admin access separate from tenant membership.
- Allow platform admins to impersonate a tenant only with explicit audit
  logging.
- Provision tenants through queued background jobs.
- Make tenant lifecycle explicit with `pending`, `active`, `suspended`,
  `archived`, and `deleted`.
- Keep archived tenants restorable.
- Support tenant-scoped backup, restore, and cloning.
- Keep the shared cache for routing metadata and tenant config only.
- Require shared cache in production.
- Use object storage as the file layer with one bucket per environment.
- Store tenant files under `tenants/{tenant_id}/...`.
- Use UUIDv4 as the default system ID format.
- Use versioned tenant config in the control plane.
- Enforce hard limits for safety-critical quotas and warning-first behavior for
  growth limits.
- Use expand-and-contract migration rollouts.
- Keep the future dedicated-tenant-database path open without changing service
  boundaries.
- Defer ontology modeling to a separate v5 note.

## Testing Decisions

- Test behavior at the module boundary, not implementation details.
- Test tenant context resolution, membership validation, and tenant switching
  as external auth behavior.
- Test RLS isolation as a security requirement with cross-tenant access
  attempts.
- Test provisioning, backup, restore, and cloning as job-driven workflows.
- Test routing target resolution and cache invalidation.
- Test audit event creation for impersonation and lifecycle changes.
- Test storage key generation and tenant-rooted path behavior.
- Test migration compatibility through schema version rollout checks.
- Prior art should follow the repo’s pattern of unit tests for pure business
  logic and integration tests for persistence and API flows.

## Out of Scope

- ontology modeling and custom object semantics
- cross-tenant business reporting
- per-tenant schema drift
- separate cluster per tenant
- self-serve tenant signup
- read replicas as a default requirement
- direct source write-back
- LLM-driven control-plane decisions

## Further Notes

This PRD is intentionally platform-focused.

It defines the multi-tenant storage, routing, and operational foundation that
future tenant-facing data products can build on. The key design principle is
that application code should stay tenant-aware, but database isolation must be
real even when the application makes a mistake.

