# V2 PRD: In-Shell Tenant Switching

## Problem Statement

The current tenant flow asks the user to choose a tenant on a separate screen
after login when no active tenant context exists. That creates an extra step
before the user can see the dashboard and makes tenant switching feel like a
pre-work gate instead of a normal workspace action.

The product needs a cleaner experience for users who belong to multiple
tenants:

- enter the app immediately after login
- default into the first tenant returned by the backend list
- switch tenants from inside the shell
- return to the dashboard after switching

The goal is to remove the separate tenant-selection page while keeping tenant
context explicit and trusted.

## Solution

Build in-shell tenant switching with automatic tenant entry after login:

- after successful login, the client reads the returned tenant list
- if at least one tenant exists, the client automatically switches into the
  first tenant in the backend-returned list
- the app opens directly on the dashboard in the active tenant context
- the shared analytics shell shows the current tenant name in a compact
  clickable control
- clicking the control opens a tenant picker inside the shell
- switching tenants always re-scopes the session and routes the user back to
  the dashboard
- no separate tenant-selection page remains in the login flow

The control should stay lightweight and visible. Tenant switching is a workspace
action, not a special setup task.

## User Stories

1. As a user with one tenant, I want to land directly inside the app after
   login, so that I do not need to make an extra selection.
2. As a user with multiple tenants, I want the system to enter my first
   backend-listed tenant automatically, so that I can start working right away.
3. As a user, I want to see my current tenant name in the shell, so that I
   always know which tenant I am working in.
4. As a user, I want to open tenant switching from the shell itself, so that I
   do not need to leave the workspace.
5. As a user, I want tenant switching to live in a compact control, so that the
   interface stays calm and efficient.
6. As a user, I want the tenant picker to list only tenants I belong to, so
   that I cannot switch into an unauthorized tenant.
7. As a user, I want the current tenant name to be the main shell label, so
   that the control stays simple.
8. As a user, I want the tenant picker to show a secondary label when names
   are similar, so that I can distinguish tenants safely.
9. As a user, I want switching tenants to always return me to the dashboard,
   so that I have a predictable landing point after context changes.
10. As a user, I want the app to keep working without a separate tenant
    selection page, so that the first-run flow feels shorter.
11. As a user, I want the active tenant context to refresh after switching, so
    that dashboard data and shell state stay in sync.
12. As a user, I want a failed tenant switch to keep me in the current tenant,
    so that I do not lose my place when a membership check fails.
13. As a user, I want the app to preserve access control during switching, so
    that tenant choice never bypasses membership rules.
14. As a user, I want the shell control to work on desktop and mobile layouts,
    so that tenant switching remains available in the responsive shell.
15. As a user, I want tenant selection to happen after login without another
    page, so that the app feels direct and not form-driven.
16. As a user, I want the system to keep tenant order deterministic, so that
    the "first tenant" behavior is predictable.
17. As a support user, I want the session to remain explicit about the active
    tenant, so that troubleshooting is straightforward.
18. As a developer, I want the tenant switching flow to remain modular and
    testable, so that the shell can change without touching unrelated pages.

## Implementation Decisions

- Keep login as an authentication step, not a tenant selection step.
- Use the backend-returned tenant list order as the source of truth for the
  automatic first-tenant entry.
- Add an in-shell tenant control in the shared analytics shell header area.
- Keep the shell label focused on the current tenant name.
- Show any secondary tenant-identifying detail only inside the picker when
  needed.
- Remove the dedicated post-login tenant-selection page.
- After a tenant switch, always route the user to the dashboard.
- Keep tenant switching in the frontend shell layer rather than introducing a
  new tenant-selection service flow.
- Keep backend membership validation in place for both login-derived session
  loading and explicit tenant switching.
- Make tenant ordering deterministic in the backend if the current query shape
  does not already guarantee stable ordering.
- Keep the existing auth and session response contract structurally compatible
  unless the ordering requirement forces a small response-shape adjustment.

## Testing Decisions

- Test behavior at the shell boundary, not implementation details.
- Test that login with tenant memberships enters the first returned tenant
  automatically.
- Test that users with multiple tenants land on the dashboard after automatic
  entry.
- Test that switching tenants from the shell updates the session and routes to
  the dashboard.
- Test that unauthorized or inactive tenant switches fail without changing the
  current tenant.
- Test that the shell shows the active tenant and exposes the picker only when
  the user has tenant choices.
- Prior art should follow the repo pattern of frontend integration tests for
  login and navigation flows, plus unit tests for shell components and session
  helpers.

## Out of Scope

- tenant administration and lifecycle management
- tenant invitation and provisioning flows
- remembering the last-used tenant across future logins
- preserving the current non-dashboard route after tenant switch
- role model changes
- backend authorization redesign
- any change that would write back to the source system

## Further Notes

This is a UX simplification, not a permissions change.

The active tenant still has to be validated by membership checks. The only
behavior change is that the app should enter the workspace more directly and
move tenant switching into the shell where users already work.
