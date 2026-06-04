# Issues: Entity Manager Property Editing and Data Studio Association

Status: draft

Parent: `doc/prd/0018-entity-manager-property-editing-and-data-studio-association.md`

These slices keep Entity Manager as the canonical semantic editor while Data
Studio stays source-prep and association context only.

1) **Entity property model + revision persistence**
- Type: AFK
- Blocked by: None
- User stories covered: 1, 2, 3, 4, 12
- What to build: Extend the Entity revision model and API so Entity Manager can create, rename, remove, and reclassify canonical properties on the active draft. Persist property identity, required/optional state, inclusion state, and display name changes as part of the Entity revision record.
- Acceptance criteria:
  - [ ] Entity revision create/update responses include editable property metadata
  - [ ] Property add/remove/rename/type/required changes persist across draft reload
  - [ ] Stable property identity survives rename
  - [ ] Publish validation still gates unresolved required properties
  - [ ] Backend tests cover property lifecycle and revision persistence

2) **Entity Manager canvas property editor**
- Type: AFK
- Blocked by: Slice 1
- User stories covered: 1, 2, 3, 4, 6
- What to build: Expose the property editing surface in the Entity Manager canvas so the user can add new properties, edit existing property metadata, and see unbound or broken properties inline. The canvas remains the primary authoring UI for Entity schema changes.
- Acceptance criteria:
  - [ ] User can add a new property from the Entity Manager canvas
  - [ ] User can edit display name, required flag, inclusion state, and type from the canvas
  - [ ] Broken or unbound properties remain visible in the canvas
  - [ ] UI state reflects draft edits before save/publish
  - [ ] Frontend tests cover property add/edit/remove flows

3) **Source binding editor and recovery flow**
- Type: AFK
- Blocked by: Slice 1, Slice 2
- User stories covered: 5, 6, 8
- What to build: Let Entity Manager bind cleaned source fields into Entity properties and recover broken bindings when source fields or datasets change. Support Data Studio-prepared source inputs, but keep the binding authoring and repair flow in Entity Manager.
- Acceptance criteria:
  - [ ] Cleaned source fields can be mapped to Entity properties in Entity Manager
  - [ ] Broken or missing bindings are visible and editable in the same surface
  - [ ] Drafts can be saved with incomplete or broken bindings where allowed
  - [ ] Publish still blocks when required bindings are unresolved
  - [ ] Backend and frontend tests cover binding persistence and recovery

4) **Data Studio association summary + deep-link**
- Type: AFK
- Blocked by: Slice 1
- User stories covered: 7, 8, 9, 10, 11
- What to build: Add a read-only Entity association summary in Data Studio that shows which Entity a dataset version feeds and provides a navigation entrypoint into Entity Manager. Keep the summary informational only; do not make Data Studio an Entity editor.
- Acceptance criteria:
  - [ ] Data Studio shows the associated Entity and active version for a dataset version
  - [ ] Data Studio provides a clear entrypoint into Entity Manager
  - [ ] Data Studio does not expose Entity property editing controls
  - [ ] Association state updates when the Entity revision changes
  - [ ] Frontend tests cover empty, loading, and associated states

5) **Boundary regression tests**
- Type: AFK
- Blocked by: Slice 1, Slice 2, Slice 3, Slice 4
- User stories covered: 1, 5, 7, 9, 11
- What to build: Add regression coverage proving the product boundary stays intact: Entity Manager owns property and binding edits, Data Studio remains source prep plus association context, and cross-surface edits do not leak schema ownership back into Data Studio.
- Acceptance criteria:
  - [ ] Entity property edits are only exposed in Entity Manager routes/components
  - [ ] Data Studio remains read-only for Entity schema
  - [ ] Association summary does not become an editor
  - [ ] Regression tests cover the end-to-end entity/edit/source-prep boundary

## Publishing Notes

- Issue tracker publishing is not performed from this draft because tracker
  configuration and triage label vocabulary were not provided in this thread.
- If publishing later, apply `needs-triage` to each issue and publish in
  dependency order: Slice 1, Slice 2, Slice 3, Slice 4, Slice 5.
