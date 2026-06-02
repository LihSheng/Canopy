# PRD: Entity Canvas Cutover and Admin Feature Flags

Status: draft

## Problem Statement

The current Entity flow is split between a step-based wizard and a separate
graph/canvas direction. That split slows the product down in two ways:

- users have to learn two editor patterns for the same semantic config
- the team has to maintain two paths while the product is still pre-launch

At the same time, the team needs a safe rollout control so the canvas cutover
can ship behind a switch, with a fallback if something regresses.

The product needs one primary editor path for Entity configuration, and it
needs a simple admin-controlled feature flag surface to govern the cutover.

## Solution

Make the Entity Designer graph canvas the only active editor path for semantic
configuration in the dataset workspace.

The canvas should:

- become the primary authoring surface for Entity mapping
- reuse the existing semantic configuration model and save/reopen contract
- persist canvas layout state in the same versioned record from day one
- support empty-state creation of the first Entity
- support source/property mapping in the canvas with quick inline actions
- keep relationship/link handling in the same canvas-based editor surface
- allow the legacy Entity tab to route into the canvas as a transition alias

To manage rollout, add a separate Admin page for global feature flags.

The feature-flag surface should:

- manage server-backed global flags that affect all users
- start as a simple list of on/off toggles with descriptions
- be controlled by a single internal Admin role for now
- gate the Entity canvas cutover during transition

This is a big-switch migration, not a long-lived dual-editor strategy. The
wizard path can remain as fallback behind the flag during the transition period,
but it is not the target end state.

## User Stories

1. As a data studio user, I want the Entity canvas to be the primary editor,
   so that I can model business meaning in one visual workspace.
2. As a data studio user, I want the legacy Entity tab to route into the
   canvas, so that I do not have to learn two editor patterns.
3. As a data studio user, I want to start from an empty Entity state, so that
   I can create the first mapping without a dead end.
4. As a data studio user, I want to map source fields to properties from the
   canvas, so that authoring stays inside the visual editor.
5. As a data studio user, I want quick inline node/property actions on the
   canvas, so that I can work without switching to a separate form flow.
6. As a data studio user, I want the canvas to use the same semantic save and
   reopen contract as the existing flow, so that my data is preserved safely.
7. As a data studio user, I want canvas layout state to persist with the saved
   mapping, so that I reopen the graph in the same arrangement.
8. As a data studio user, I want the canvas to support source/property mapping
   first, so that the core authoring path is available early.
9. As a data studio user, I want relationship links to live in the same
   canvas-based editor, so that the Entity model stays in one place.
10. As a data studio user, I want the wizard fallback to remain available
    during transition, so that the rollout can be reversed if needed.
11. As a platform operator, I want the Entity cutover to be behind a feature
    flag, so that rollout can be controlled safely.
12. As a platform operator, I want feature flags to affect all users globally,
    so that release control is consistent.
13. As an Admin user, I want a separate feature-flag page, so that I can manage
    operational rollout controls without touching the Entity editor.
14. As an Admin user, I want to toggle global flags on and off, so that I can
    enable or disable product behavior quickly.
15. As an Admin user, I want simple descriptions next to each flag, so that I
    understand what each control changes.
16. As an internal operator, I want one admin role to manage flags for now, so
    that permissions stay simple until tighter gating is needed.
17. As a future feature owner, I want the flag system to stay server-backed,
    so that behavior is consistent for every user.

## Implementation Decisions

- The Entity Designer graph canvas is the only active editor path for Entity
  configuration.
- The legacy Entity tab remains only as a route alias during the transition.
- The migration is a big switch, not a staged dual-editor strategy.
- The canvas uses the same backend save/reopen contract as the existing flow.
- Layout state is part of the persisted versioned snapshot from day one.
- Source/property mapping is the first canvas slice.
- Empty-state Entity creation is in scope for the first cutover.
- Relationship links remain part of the same canvas-based editor surface.
- The canvas may include quick inline actions, but only for node/property
  mapping in the first slice.
- Source registration can stay separate until the core canvas mapping path is
  stable.
- The feature flag system is server-backed and global.
- Feature flags are managed from a separate Admin page.
- The first Admin page version is a simple list of on/off toggles with
  descriptions.
- One internal Admin role manages feature flags for now.
- The feature flag surface exists in the same implementation wave as the
  canvas cutover.
- The backend semantic model remains `semantic_*` for now.
- The Entity configuration remains dataset-scoped and versioned.

## Testing Decisions

- Good tests verify external behavior, not implementation details.
- Canvas tests should cover visible mapping behavior, empty state, save/reopen,
  and fallback behavior under the feature flag.
- Feature-flag tests should cover toggle persistence, page rendering, and
  access control for the Admin surface.
- Save/reopen contract tests should prove the canvas uses the same backend
  payload and layout snapshot model as the current Entity flow.
- Modules to test:
  - canvas node/property mapping behavior
  - empty-state Entity creation
  - versioned save/reopen behavior
  - layout state persistence
  - route alias behavior for the legacy Entity tab
  - server-backed feature flag CRUD/toggle behavior
  - Admin access control for feature flags
- Prior art:
  - existing frontend wizard tests for Entity mapping flow
  - existing backend semantic API and validation tests
  - existing dataset workspace component tests

## Out of Scope

- Tenant-wide graph browsing
- Long-lived parallel wizard and canvas editors
- New canvas-specific payload format for the initial cutover
- Per-user feature flags
- Per-dataset feature flags for the new admin surface
- Complex segmented rollout controls beyond simple global on/off toggles
- Dev-only flag management hidden outside the app admin surface
- Runtime entity hydration
- Executable joins or semantic engine execution

## Further Notes

This PRD is the migration step that turns the graph-first direction into the
single supported authoring path.

The intended progression is:

1. Entity canvas becomes the primary authoring path
2. Legacy Entity tab becomes a route alias
3. Admin feature flags manage rollout globally
4. The old wizard path is removed after cutover stabilizes

The project should keep the existing semantic config model and only change the
authoring surface and rollout control around it.
