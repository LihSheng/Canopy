# Tenant Access Context

## Goal

Implement global login, tenant switching, and request-scoped tenant context so
every authenticated request resolves to one active tenant.

## Tasks

- [x] Add login flow support for global user identities in the control plane.
- [x] Add tenant membership lookup after login.
- [x] Add tenant switch action in the UI.
- [x] Re-issue the JWT when the active tenant changes.
- [x] Build request-scoped tenant context from the active token.
- [x] Revalidate tenant membership on authenticated entrypoints.
- [x] Block access when the user is not a member of the requested tenant.
- [x] Carry impersonation state in the tenant context.

## Testing

- [x] Add unit tests for tenant context creation and membership validation.
- [x] Add integration tests for login and tenant switch behavior.
- [x] Add regression tests that ensure unauthorized tenant access is denied.

