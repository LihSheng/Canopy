# Tenant Backup, Restore, And Cloning

## Goal

Implement tenant-scoped backup, restore, and cloning with PITR semantics and
auditable admin control.

## Tasks

- [x] Add backup policy records per tenant.
- [x] Add automated backup jobs with PITR support.
- [x] Add restore jobs with tenant-scoped validation.
- [x] Add clone jobs that copy the full tenant database by default.
- [x] Keep archived tenants restorable until retention expiry.
- [x] Record backup, restore, and clone results in the control plane.
- [x] Refresh routing metadata after restore or clone completion.

## Testing

- [x] Add unit tests for backup policy and restore validation.
- [x] Add integration tests for backup, restore, and clone flows.
- [x] Add regression tests that ensure a tenant restore does not affect other
  tenants.

