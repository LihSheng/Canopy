# Control Plane Provisioning

## Goal

Implement the shared control plane for tenant registry, memberships, lifecycle
state, config, provisioning, audit, and platform admin operations.

## Tasks

- [x] Create control-plane schema for users, tenants, memberships, config,
  jobs, and audit.
- [x] Add tenant lifecycle states and versioned config storage.
- [x] Add platform admin tenant creation flow.
- [x] Queue tenant provisioning jobs from the control plane.
- [x] Persist provisioning status and failures.
- [x] Add tenant suspend, restore, and archive flows.
- [x] Add platform admin impersonation with explicit audit events.
- [x] Add tenant routing metadata storage.
- [ ] Add shared cache invalidation on lifecycle and config changes. (→ Sub-agent 5)

## Testing

- [x] Add unit tests for lifecycle transitions and config versioning.
- [x] Add integration tests for tenant provisioning and status tracking.
- [x] Add audit tests for impersonation and admin lifecycle actions.
