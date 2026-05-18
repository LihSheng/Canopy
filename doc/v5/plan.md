# V5 Plan

## Purpose

This document is the planning entrypoint for v5.

V5 is the future multi-tenant platform and database architecture phase. It
defines the control-plane and tenant-data split, the routing model, and the
operational guardrails needed to support tenant isolation cleanly.

## Baseline

V4 is the workspace and dataset phase.

V5 sits above that foundation and adds platform-level tenant management:

- tenant provisioning
- tenant membership and switching
- tenant-aware storage routing
- database isolation and RLS enforcement
- tenant-scoped backup and restore
- tenant-scoped quotas and job fairness
- platform admin and impersonation flows

## V5 scope

V5 delivers:

- shared control plane database
- shared tenant data database for the current stage
- request-scoped tenant context
- tenant-aware routing with JWT re-issue on tenant switch
- PostgreSQL RLS for tenant-owned tables
- object storage with tenant-rooted paths
- platform admin tenant provisioning
- tenant lifecycle management
- tenant-scoped backup, restore, and cloning
- tenant config and feature flags
- shared cache for routing and tenant config metadata
- expand-and-contract migration pipeline

V5 does not deliver:

- ontology modeling
- cross-tenant business reporting
- per-tenant schema drift
- self-serve tenant signup
- direct source write-back
- read replicas as a default requirement
- separate cluster per tenant

## Confirmed requirements

- one PostgreSQL cluster
- one separate control-plane database in the same cluster
- one shared tenant data database for the current stage
- future move to dedicated per-tenant databases remains supported
- `tenant_id` is a UUID and remains portable across storage splits
- UUIDv4 is the default ID format for system entities
- tenant isolation uses application context plus PostgreSQL RLS
- the application uses `SET LOCAL app.current_tenant_id = '...'` inside a
  transaction
- platform admins can impersonate a tenant context with audit logging
- platform admins provision tenants through queued background jobs
- tenant lifecycle is explicit and restorable
- tenant-scoped backups use PITR
- quotas are hard enforced for safety-critical limits and warning-first for
  growth limits
- shared cache is required in production for routing and tenant config

## Architecture guardrails

V5 planning must preserve:

- modular monolith boundaries
- request-scoped tenant context, not global mutable state
- explicit control-plane and tenant-data separation
- database-enforced isolation, not app-only trust
- non-blocking, backward-compatible migrations
- tenant-scoped backups, restores, and cloning

## Suggested next v5 docs

When v5 scope is chosen, create:

- `doc/v5/database-architecture.md`
- `doc/v5/high-level-design.md`
- `doc/v5/detailed-design.md`
- `doc/v5/ontology-todo.md`

