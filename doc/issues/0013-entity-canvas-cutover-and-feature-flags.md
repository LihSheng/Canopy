# Issue 13: Entity Canvas Cutover and Admin Feature Flags

## Parent

PRD: `doc/prd/0013-entity-canvas-cutover-and-feature-flags.md`

## What to build

Deliver the graph/canvas as the only active Entity editor path behind a
global feature flag, and add an Admin page for server-backed global feature
flags. The canvas must reuse the existing semantic save/reopen contract and
persist layout state from day one. The legacy Entity tab should remain as a
route alias during transition.

## Acceptance Criteria

- [ ] The Entity canvas is the primary editor path for dataset-scoped Entity
      configuration.
- [ ] The legacy Entity tab routes into the canvas and no longer exposes a
      separate editor experience.
- [ ] The canvas supports empty-state Entity creation.
- [ ] The canvas supports source/property mapping with quick inline actions.
- [ ] The canvas uses the existing semantic save/reopen contract.
- [ ] Canvas layout state is persisted with the versioned mapping record.
- [ ] Relationship links remain in the canvas-based editor surface.
- [ ] The old wizard path remains available only as a feature-flagged fallback
      during transition.
- [ ] `Admin > Feature Flags` exists as a separate page.
- [ ] Feature flags are server-backed, global, and on/off only in v1.
- [ ] Feature-flag rows show a short description.
- [ ] The Admin feature-flag page is restricted to the internal Admin role.
- [ ] Backend and frontend tests cover the canvas cutover path, fallback
      routing, save/reopen parity, layout persistence, and feature-flag admin
      behavior.

## Blocked by

- None

## Notes

- Keep the initial migration big-switch oriented.
- Preserve the current `semantic_*` model underneath.
- Do not introduce a new canvas-only payload format for the first cutover.
