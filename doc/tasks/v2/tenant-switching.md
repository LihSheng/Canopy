# Tenant Switching Module Tasks

## Goal

Replace the separate post-login tenant selection page with an in-shell tenant
switcher. The app should auto-enter the first backend-returned tenant after
login, show the current tenant name in the shared shell, and always return the
user to the dashboard after a tenant switch.

## Scope

This slice covers the end-to-end tenant-switching flow:

- login
- automatic entry into the first tenant returned by the backend
- active tenant display in the analytics shell
- in-shell tenant picker
- tenant switch action
- dashboard redirect after switch
- test coverage for the behavior above

It does not cover tenant administration, invitations, lifecycle management, or
memory of the last-used tenant across future logins.

## Execution Rules

- Keep the login step as authentication only.
- Use the backend-returned tenant list order as the source of truth for the
  initial auto-entered tenant.
- Remove the separate post-login tenant-selection screen.
- Put tenant switching inside the shared analytics shell, not on a standalone
  page.
- Show the current tenant name in the shell; keep the label compact.
- If the picker needs disambiguation for similar tenant names, show secondary
  detail inside the picker only.
- After a tenant switch, always route the user to `/dashboard`.
- Keep membership validation in place for both initial session resolution and
  explicit switching.
- Keep the implementation narrow and readable. Do not broaden this into a
  general auth rewrite.

## Tasks

- [ ] Make the backend tenant list order deterministic so the first tenant is
  stable and intentional.
- [ ] Update the login flow to automatically switch into the first returned
  tenant after successful authentication.
- [ ] Remove the separate post-login tenant-selection page.
- [ ] Add a compact current-tenant control to the analytics shell header or
  sidebar header area.
- [ ] Add an in-shell tenant picker that lists only the user’s available
  tenants.
- [ ] Make tenant switching always redirect to the dashboard.
- [ ] Ensure failed or unauthorized tenant switches keep the current tenant
  unchanged.
- [ ] Keep session loading and tenant context refresh in sync after switch.
- [ ] Update or add frontend tests for login auto-entry and shell switching.
- [ ] Update or add backend tests for tenant list ordering and membership
  validation if the ordering work changes the contract.

## Suggested Module Boundaries

- `auth` service and route handling for session and tenant switching
- shared analytics shell header area for the tenant control
- login page / session guard flow for auto-enter behavior
- tenant picker component for the in-shell selection UI
- frontend auth and shell tests for behavior coverage
- backend auth tests for deterministic ordering and membership checks

## Acceptance Criteria

- [ ] A user with tenants lands directly in the app after login.
- [ ] The first backend-returned tenant becomes the active tenant by default.
- [ ] The separate tenant-selection page no longer appears after login.
- [ ] The shell shows the active tenant name and provides a switch control.
- [ ] Switching tenants from the shell always returns the user to the
  dashboard.
- [ ] Unauthorized or inactive tenant switching is rejected.
- [ ] The active tenant context stays explicit after switching.
- [ ] Automated tests cover the login, auto-entry, switch, and redirect flow.

## Testing

- Test behavior at the route and shell boundary, not implementation details.
- Add frontend coverage for login auto-entry into the first tenant.
- Add frontend coverage for shell-based tenant switching and dashboard
  redirect.
- Add frontend coverage for the empty-tenants case if the app can reach it.
- Add backend coverage for membership validation during switch.
- Add backend coverage for deterministic tenant ordering if the backend query
  shape changes.

## Notes For The Implementer

The main product decision is already fixed:

- no tenant selection page after login
- auto-enter first backend-returned tenant
- shell-based tenant switching
- always return to dashboard after switch

The remaining work is implementation detail, test coverage, and keeping the
contract stable.
