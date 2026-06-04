# PRD: Entity Add Flow With Palantir-Style Helper

Status: draft

Builds on and refines:

- PRD 0015 Entity Manager Registry, Detail, and Editor Split
- PRD 0017 Entity-First Digital Twin Manager
- PRD 0018 Entity Manager Property Editing and Data Studio Association

## Problem Statement

The current Entity experience needs a single, understandable creation flow.
Users should be able to start from either the Entity registry or a dataset,
then choose whether they are creating a brand-new Entity or attaching a dataset
to an existing Entity.

Without a clear helper, the product risks splitting the same semantic task into
multiple overlapping editors:

- registry-based Entity creation
- dataset-based Entity bootstrap
- dataset-scoped semantic editing
- entity-first inspection and management

The user wants the flow to feel closer to Palantir's object type helper:

- start from a helper, not a blank technical form
- optionally choose a backing datasource
- provide object metadata first
- configure properties and primary key selection
- optionally preview actions
- save the Entity shell immediately
- continue into the canonical Entity manager

The product also needs to preserve Canopy's current boundary rules:

- Entity Manager is the canonical authoring surface
- Data Studio remains the source preparation surface
- source data is attached into Entities, not treated as the semantic owner
- the helper should not become a second permanent editor

## Solution

Add a single Entity creation helper that supports two entry modes:

- create a new Entity
- attach a dataset to an existing Entity

The user may start from either the central Entity registry or a dataset page.
In both cases, the helper must resolve into the same canonical Entity Manager
shell.

The helper should follow a Palantir-style order:

1. user chooses create new or attach existing
2. user optionally chooses or skips a backing datasource
3. user enters metadata
4. user configures properties, primary key, and title key
5. user sees a preview-only actions step
6. user creates the Entity shell immediately
7. user lands in the Entity detail/manager flow

The documented helper step sequence should be treated as the design reference:

- Datasource
- Metadata
- Properties
- Actions
- Save location

Important behavioral details from the reference:

- the datasource step offers both `continue without datasource` and `use existing datasource`
- the metadata step includes icon, name, plural name, description, and groups
- the properties step includes primary key and title selection
- the properties step supports manual property row editing and adding rows
- the actions step is generated as a guided step, not a free-form action editor
- the last step is a save-location / create confirmation step
- save happens as the explicit final action

If the user attaches an existing Entity, the helper should search first and then
fork a draft before changes are made. If the user creates a new Entity, the
helper should generate a stable object type key from the initial name on the
server and keep that key fixed afterward.

The helper should be source-aware but not source-owned:

- datasource step is optional
- no empty backing dataset is created when datasource is skipped
- dataset attachment remains a bootstrap action, not a separate editor
- relationship links stay outside the initial create helper

## User Stories

1. As a data modeler, I want to start Entity creation from the registry, so
   that I can model a business object without first opening a dataset.
2. As a data modeler, I want to start Entity creation from a dataset, so that
   I can bootstrap an Entity from source data when that is the fastest path.
3. As a data modeler, I want to choose between create new and attach existing,
   so that I can use the right entry mode for the task.
4. As a data modeler, I want the helper to use one shared flow after the choice,
   so that I do not learn two different Entity create experiences.
5. As a data modeler, I want the helper to follow a Palantir-like order, so
   that the flow feels familiar and structured.
6. As a data modeler, I want datasource selection to be optional, so that I can
   create a blank Entity when no source is ready yet.
7. As a data modeler, I want to skip datasource creation without generating an
   empty backing dataset, so that I do not create storage I do not need.
8. As a data modeler, I want to enter Entity metadata early, so that the shell
   has a stable identity before I continue.
9. As a data modeler, I want to provide display name, plural name, description,
   icon, and groups, so that the Entity registry has a complete object record.
10. As a data modeler, I want the object type key to be generated from the
    initial name, so that technical identity stays stable without manual work.
11. As a data modeler, I want the generated object type key to stay fixed after
    create, so that later renames do not silently change identity.
12. As a data modeler, I want to define properties during creation, so that the
    Entity can be shaped before I publish it.
13. As a data modeler, I want to pick one primary key, so that entity identity
    stays explicit.
14. As a data modeler, I want the helper to help me choose a title key, so that
    the Entity has a human-readable display field.
15. As a data modeler, I want the helper to auto-pick a likely title key when
    it can infer one, so that common cases are fast.
16. As a data modeler, I want to preview actions without configuring them fully,
    so that the helper stays focused on object setup.
17. As a data modeler, I want the Entity shell to save immediately, so that the
    registry reflects in-progress work and I do not lose progress.
18. As a data modeler, I want the helper to land me in the Entity manager after
    create, so that I can keep working in one canonical surface.
19. As a data modeler, I want the registry to show incomplete shells, so that I
    can return to in-progress setup later.
20. As a data modeler, I want a distinct in-progress status, so that unfinished
    Entities are easy to distinguish from published ones.
21. As a data modeler, I want attach-existing to search first, so that I can
    find the right Entity quickly.
22. As a data modeler, I want attach-existing to offer recent or suggested
    Entities, so that frequent choices are easy to reach.
23. As a data modeler, I want attach-existing to fork a draft before editing,
    so that I do not mutate a live published contract directly.
24. As a data modeler, I want dataset bootstrap to attach the dataset into the
    existing Entity, so that I can reuse a business object rather than create a
    duplicate.
25. As a data modeler, I want relationship links to stay out of the initial
    helper, so that the first release remains governable.
26. As a platform operator, I want the helper to preserve the existing Entity
    module boundary, so that the registry and manager remain the canonical home.
27. As a platform operator, I want the dataset page entrypoint to be a router
    into the Entity manager, so that Data Studio does not become a second editor.
28. As a platform operator, I want the create flow to produce a stable object
    identity, so that downstream references do not drift.
29. As a future feature owner, I want the helper to stay narrow, so that later
    actions, links, and richer bootstrap steps can be added without rewriting
    the create experience.

## Implementation Decisions

- Keep one canonical Entity helper that supports both create-new and
  attach-existing entry modes.
- Show the entry choice in a modal when the user clicks Add Entity.
- Keep the helper shared after the choice; do not create two separate wizards.
- Treat the central Entity module as the canonical landing surface.
- Treat dataset workspace entrypoints as deep links into the same Entity flow.
- For create-new, start with a datasource step, then metadata, then properties,
  then actions, then save location.
- For attach-existing, search existing Entities first, then let the user fork a
  draft and attach the dataset.
- Make datasource optional.
- If datasource is skipped, create the Entity shell without requiring a
  source-backed dataset.
- Collect metadata fields early: display name, plural name, description, icon,
  and groups.
- Generate `object_type_key` on the server from the initial name.
- Keep `object_type_key` stable after creation.
- Save the Entity shell immediately when create completes.
- Open the new Entity detail/manager flow immediately after shell creation.
- Require one primary key during setup.
- Provide title key selection in the helper.
- Auto-pick a likely title key when the schema makes it obvious, but let the
  user confirm or override it.
- Present an actions step as preview-only in the helper.
- Keep relationship links out of the initial helper.
- Surface incomplete shells in the registry with a distinct in-progress state.
- Keep attach-existing search-first with recent and suggested Entities.
- Keep the first create flow focused on Entity shell creation, property setup,
  and canonical source attachment, not on full semantic runtime behavior.
- Preserve the product term `Entity` and the internal implementation term
  `semantic_*` where already established.

## Testing Decisions

- Good tests verify external behavior and state transitions, not component
  internals.
- The helper should be tested as a user flow, including entry choice, branch
  selection, and post-create navigation.
- The registry should be tested for in-progress shell visibility and status.
- The attach-existing path should be tested for search, recent suggestions,
  draft fork behavior, and dataset attachment.
- The create-new path should be tested for generated key behavior, required
  property flow, title key flow, and immediate shell persistence.
- The dataset entrypoint should be tested only as a route into the canonical
  Entity manager, not as a second editor.
- Backend tests should cover:
  - object type key generation from initial name
  - object type key stability after rename
  - shell creation and immediate visibility
  - draft fork behavior for attach-existing
  - helper validation for primary key and title key selection
  - optional datasource branch behavior
- Frontend tests should cover:
  - modal entry choice
  - shared helper branch behavior
  - create-new and attach-existing navigation
  - in-progress registry status
  - preview-only actions step
- Prior art in the codebase includes existing entity registry tests, entity
  detail tests, semantic mapping wizard tests, and entity canvas tests.

## Out of Scope

- Full relationship-link authoring inside the initial create helper
- Runtime entity browsing or object explorer behavior
- Empty backing dataset creation when datasource is skipped
- Replacing the current Entity manager with a separate product surface
- Full action configuration in the helper
- Multi-user collaborative draft editing
- Automatic key regeneration on rename
- Reworking the semantic storage model in the same slice

## Further Notes

The agreed product shape is now:

1. Entity registry or dataset page opens the same add flow.
2. User chooses create new or attach existing.
3. Shared helper guides the user through datasource, metadata, properties,
   title key, and preview-only actions.
4. Create saves the shell immediately.
5. The user lands in the canonical Entity manager.

This keeps the product Palantir-like in flow while preserving Canopy's module
boundaries and read-only source policy.
