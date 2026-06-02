# PRD: Entity Designer Graph Canvas

Status: draft

## Problem Statement

The current dataset-scoped Entity mapping flow is usable, but it is still too
form-driven for the product direction we want.

Users need to understand how raw data becomes a business entity. They need to
see the source objects, the dataset version, the Entity, and the links between
source fields and Entity properties in one visual workspace.

Without that visual layer:

- the relationship between raw data and Entity config remains hard to grasp
- non-technical users still have to think in form steps instead of a data map
- the product cannot express the "raw source -> dataset -> entity" story that
  the Palantir-style canvas makes obvious

The platform needs a graph-first Entity designer that still saves the same
versioned semantic configuration model.

## Solution

Add an Entity Designer graph canvas inside the Dataset Workspace.

The graph should let a user:

- see the current dataset lineage path
- see the current Entity and any existing source references
- create or register source nodes from the canvas for known dataset tables or
  static files
- reuse source nodes across multiple Entities
- connect multiple source nodes into a single Entity
- map one source field to one Entity property
- inspect and edit nodes and edges in a right-side drawer
- save the graph as an explicit versioned mapping record
- reopen the graph with the same semantic config and layout state

The phase-1 graph is dataset-scoped and current-dataset-scoped only:

- no tenant-wide graph
- no process nodes
- no full connector import flow from the canvas
- no computed multi-field properties
- no runtime entity hydration
- no executable join generation

## User Stories

1. As a data studio user, I want to open an Entity graph inside a dataset, so
   that I can design business meaning visually without leaving the workspace.
2. As a data studio user, I want to see the current dataset lineage path on
   the graph, so that I understand how raw data reaches the Entity.
3. As a data studio user, I want to see the current Entity node, so that I can
   understand what business object I am designing.
4. As a data studio user, I want to see existing links and references, so that
   I understand what is already connected.
5. As a data studio user, I want to create a source node from the canvas, so
   that I do not have to leave the Entity workspace to start modeling.
6. As a data studio user, I want to register an already known table or file
   source from the canvas, so that I can attach existing raw data quickly.
7. As a data studio user, I want source nodes to support dataset tables and
   static files, so that I can model both structured and file-based inputs.
8. As a data studio user, I want source nodes to be reusable across multiple
   Entities, so that I do not duplicate source setup.
9. As a data studio user, I want to connect multiple source nodes to one
   Entity, so that one business object can be formed from more than one input.
10. As a data studio user, I want source nodes to be unordered in the Entity
    config, so that the model stays simple and does not imply false precedence.
11. As a data studio user, I want to inspect a node in a right-side drawer, so
    that I can edit details without losing the canvas context.
12. As a data studio user, I want to inspect an edge in a right-side drawer, so
    that I can adjust a mapping or link directly from the graph.
13. As a data studio user, I want the Entity/Object Type node to be editable in
    the graph, so that the graph itself is the primary authoring surface.
14. As a data studio user, I want source and dataset nodes to remain read-only,
    so that system facts cannot be edited accidentally.
15. As a data studio user, I want source fields to be collapsed by default, so
    that the graph stays readable even when a source has many columns.
16. As a data studio user, I want to expand a source node and see its fields in
    the drawer, so that I can choose the right source field.
17. As a data studio user, I want to map one source field to one Entity
    property, so that each property has one clear origin.
18. As a data studio user, I want to see source-field-to-property edges, so
    that the mapping is visually explicit.
19. As a data studio user, I want to build an Entity from multiple source
    fields and multiple source nodes, so that real-world objects can be
    composed from several raw inputs.
20. As a data studio user, I want to add target references visually, so that I
    can understand how this Entity relates to other tenant Object Types.
21. As a data studio user, I want the graph to show only the current dataset's
    scope plus target references, so that I am not overwhelmed by the whole
    tenant at once.
22. As a data studio user, I want an empty Entity state when no mapping exists,
    so that I can start from a clear prompt instead of a dead end.
23. As a data studio user, I want the graph to allow creating the first Entity
    from the empty state, so that I can start modeling immediately.
24. As a data studio user, I want an explicit Save/Publish button, so that I
    can review changes before committing them.
25. As a data studio user, I want graph changes to create a new versioned
    mapping record, so that history is preserved.
26. As a data studio user, I want the graph to reopen with the same semantic
    config and canvas layout, so that I do not lose my arrangement.
27. As a data studio user, I want the canvas to accept both dataset-table and
    static-file sources, so that I can model both kinds of inputs in one flow.
28. As a platform operator, I want the graph editor to stay dataset-scoped, so
    that the boundary remains safe and predictable.
29. As a platform operator, I want the saved graph state to remain durable in
    database tables, so that Entity designs are auditable and editable.
30. As a future feature owner, I want the graph config to remain portable as
    JSON later, so that a future semantic engine can consume it.
31. As a future feature owner, I want the graph layout to be versioned too, so
    that the visual authoring experience can be restored accurately.

## Implementation Decisions

- The feature is graph-first Entity design for the dataset workspace.
- UI naming uses `Entity`, not `Ontology`.
- Internal naming can stay `semantic_*` where the backend already uses it.
- The graph is scoped to the current dataset and dataset version.
- The graph is the primary workspace; the detail editor lives in a right-side
  drawer and reuses the existing wizard logic patterns.
- The graph must be editable, not read-only.
- The graph save action is explicit and produces a new versioned mapping
  record.
- Version snapshots must include both semantic config and canvas layout state.
- The graph load should show the current dataset lineage path, the current
  Entity, and existing links or references.
- The graph can create or register source nodes from the canvas, but only for
  already known dataset tables or static files.
- Source nodes are reusable across multiple Entities.
- An Entity can connect to multiple source nodes.
- Source nodes are unordered in the saved config.
- Source nodes default to collapsed field lists and expand in the drawer when
  selected.
- Source-field-to-property edges are the canonical mapping shape.
- One source field maps to one Entity property in phase 1.
- Computed multi-field properties are out of scope for this slice.
- Source and dataset nodes remain read-only in the drawer.
- The canvas can show target references for existing tenant Object Types, but
  the graph remains current-dataset scoped rather than tenant-wide.
- The source creation drawer is lightweight and does not launch the full Data
  Studio connector import flow.
- The saved artifact should remain representable as JSON later for future
  semantic consumption.

## Testing Decisions

- Good tests verify external behavior, not implementation details.
- Graph behavior should be covered through component and flow tests that verify
  visible nodes, edges, drawer behavior, and save actions.
- State serialization and version snapshot logic should be covered with pure
  tests wherever possible.
- Backend contracts should be covered with integration tests for graph
  persistence, versioning, and readback.
- Modules to test:
  - graph state normalization
  - node and edge edit behavior
  - source registration behavior
  - versioned save and reopen behavior
  - layout persistence and restoration
  - source-field-to-property validation
- Prior art:
  - existing frontend wizard tests for mapping flows
  - existing backend semantic API and validation tests
  - existing dataset workspace component tests

## Out of Scope

- Tenant-wide graph browsing
- Process nodes such as clean, group, or transform steps
- Full connector import onboarding from the canvas
- Runtime entity hydration
- Executable joins generated from the graph
- Computed properties from multiple source fields
- Multi-field property formulas
- Cross-dataset graph composition
- Central entity registry page
- Cross-tenant relationships
- Ontology storage redesign

## Further Notes

This PRD is the visual successor to the dataset-scoped Entity mapping work.

The intended progression is:

1. Data Studio connection and dataset workbench
2. Dataset Entity mapping
3. Graph-first Entity designer with canvas editing and versioned layout
4. Later relationship/semantic/runtime consumption, if and when that is
   promoted from config-only to runtime behavior

The phase-1 graph is intentionally bounded to the current dataset context, but
it should still feel like a business-object designer rather than a narrow form.
