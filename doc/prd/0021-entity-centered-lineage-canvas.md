# PRD: Entity-Centered Lineage Canvas

Status: draft

Builds on and clarifies:

- PRD 0011 Entity Designer Graph Canvas
- PRD 0015 Entity Manager Registry, Detail, and Editor Split
- PRD 0017 Entity-First Digital Twin Manager
- PRD 0018 Entity Manager Property Editing and Data Studio Association

## Problem Statement

The current Entity canvas is still organized around dataset-backed mapping
behavior. That makes the canvas hard to reason about when the user's real goal
is to understand how an Entity is formed from source data.

Today, users expect the Entity surface to answer a different question:

- what is the Entity
- which dataset and dataset version feed it
- which source nodes contribute to it
- which properties are bound to which source fields
- which intermediate transformation steps exist in the lineage path

The current implementation still mixes several concepts together:

- dataset association
- semantic mapping persistence
- publish gating
- canvas rendering
- source binding management

That coupling creates two problems:

- some valid Entity drafts do not show a canvas because they do not yet have a
  persisted dataset-backed mapping
- the graph shape is too narrow to grow into a real lineage view without a
  later rewrite

The product needs an Entity-centered lineage canvas that can grow into richer
lineage depth later while still working for today's direct source-to-Entity
cases.

## Solution

Make the Entity canvas Entity-centered and lineage-first.

The canvas should:

- center the Entity as the primary node
- show the backing Dataset and active Dataset Version as upstream context
- show source nodes that feed into the Dataset Version
- show direct property bindings from source fields into the Entity
- show simple Entity-to-Entity links as edges
- render existing derived lineage nodes when they exist
- support collapse/expand for derived chains only
- load fully expanded by default
- keep the initial graph simple while preserving a storage shape that can grow

The graph should preserve the current semantic editing job:

- Entity properties remain visible as labels on the Entity node first
- source bindings remain explicit
- Data Studio remains the source-preparation surface
- Entity Manager remains the semantic modeling surface

This is not a full ontology graph. It is a focused Entity lineage canvas with a
clean path to more depth later.

## User Stories

1. As a data modeler, I want the Entity to be the center of the canvas, so
   that the graph matches the business object I am editing.
2. As a data modeler, I want to see the Dataset and Dataset Version in the
   canvas, so that I can understand the source context without leaving the
   Entity surface.
3. As a data modeler, I want to see source nodes that feed the Entity, so that
   I can trace where the data comes from.
4. As a data modeler, I want source nodes to connect into the Dataset Version,
   so that the lineage path stays explicit.
5. As a data modeler, I want the Dataset to connect to the Dataset Version
   with a normal edge, so that the graph stays composable.
6. As a data modeler, I want the Dataset Version to connect to the Entity, so
   that the overall path reads as lineage.
7. As a data modeler, I want to see property names on the Entity node first,
   so that the canvas stays readable.
8. As a data modeler, I want property bindings to remain visible in the graph,
   so that the origin of each property is transparent.
9. As a data modeler, I want source-field-to-property edges, so that mapping
   intent is visible at a glance.
10. As a data modeler, I want to bind one source field to one Entity property
    in the first release, so that the mapping rules stay clear.
11. As a data modeler, I want intermediate derived nodes to be supported later,
    so that the canvas can grow into richer lineage without a redesign.
12. As a data modeler, I want existing derived nodes to render when they are
    already stored, so that future lineage depth appears naturally.
13. As a data modeler, I want derived chains to collapse and expand, so that
    the graph remains usable as lineage grows.
14. As a data modeler, I want collapsed derived chains to summarize with the
    last visible label plus hidden-step count, so that I can still understand
    what is hidden.
15. As a data modeler, I want the graph to be fully expanded on load, so that
    I do not have to open the important context manually.
16. As a data modeler, I want Entity-to-Entity links to remain simple edges,
    so that relationship metadata does not overwhelm the canvas.
17. As a data modeler, I want richer entity relationship semantics to live in
    a future ontology-level graph, so that the Entity canvas stays focused.
18. As a data modeler, I want the canvas to show only the direct upstream path
    into the Entity, so that I am not distracted by unrelated branches.
19. As a data modeler, I want the canvas to avoid sibling branches by default,
    so that the surface stays about the Entity I am editing.
20. As a data modeler, I want the graph storage to use a generic lineage node
    model, so that new node kinds do not require a storage rewrite.
21. As a data modeler, I want node kinds such as dataset, source, derived, and
    entity, so that the graph can represent each lineage stage clearly.
22. As a data modeler, I want derived to remain broad at first, so that we do
    not overfit the model to one pipeline shape.
23. As a data modeler, I want optional subtype metadata for derived nodes
    later, so that clean, enrich, and other stages can be labeled when needed.
24. As a data modeler, I want manual creation of derived nodes to wait until
    the persistence model is ready, so that the UI does not invent unsupported
    graph structure.
25. As a platform operator, I want the Entity canvas to be implemented with a
    durable data model, so that future lineage depth does not force a rewrite.
26. As a platform operator, I want Entity publish to be independent from the
    presence of a dataset-backed canvas link, so that valid drafts can publish
    without a legacy dataset requirement.
27. As a platform operator, I want the Entity canvas to remain separate from a
    future ontology graph, so that relationship semantics do not become mixed.
28. As a future feature owner, I want the first canvas schema to already allow
    derived nodes and collapse state, so that later lineage work is additive.

## Implementation Decisions

- The Entity canvas is Entity-centered.
- The Dataset and Dataset Version remain visible as upstream context.
- The graph follows a direct upstream path only in the first release.
- Source nodes connect into the Dataset Version, not directly into the Entity.
- The Dataset connects to the Dataset Version with a normal edge rather than
  visual nesting.
- Derived nodes may exist both before the Dataset Version and between the
  Dataset Version and the Entity.
- Derived nodes are rendered when they already exist in stored lineage data.
- Manual creation of derived nodes is out of scope for the first pass.
- The graph should default to fully expanded on load.
- Collapse/expand should apply to derived chains only at first.
- A collapsed derived chain should summarize as the last visible node label
  plus a hidden-step count.
- Entity properties should be shown as labels on the Entity node first.
- Separate property nodes can be added later if the graph needs more detail.
- Entity-to-Entity links remain simple edges.
- Richer entity relationship semantics belong in a future ontology-level graph,
  not in the Entity canvas.
- The graph storage model should be generic and lineage-oriented:
  - node kind: dataset
  - node kind: source
  - node kind: derived
  - node kind: entity
  - edge kind: lineage
  - edge kind: binding
  - edge kind: link
- The implementation should not treat dataset_id as the primary determinant of
  whether the canvas exists.
- The Entity detail page should be able to render the canvas from draft
  revision and lineage data even when no legacy dataset-backed mapping exists.
- The canvas should preserve compatibility with existing semantic mapping data
  while moving toward the generic lineage model.

## Testing Decisions

- Good tests verify visible graph behavior and persisted contract behavior,
  not internal rendering details.
- Frontend tests should cover:
  - Entity-centered canvas rendering
  - dataset/version visibility
  - direct upstream path rendering
  - source-to-dataset-version edge direction
  - property label visibility on the Entity node
  - derived chain collapse and expansion
  - full expansion on initial load
- Backend tests should cover:
  - publish without requiring a dataset-backed mapping
  - persisted lineage data shape support for the generic node model
  - compatibility with existing semantic mapping records
- Prior art:
  - existing Entity detail page tests
  - existing semantic revision integration tests
  - existing graph canvas tests

## Out of Scope

- Full ontology graph semantics
- Arbitrary sibling-branch exploration
- Manual creation of derived nodes before persistence support exists
- Runtime execution of lineage transforms
- Replacing Data Studio as the source-preparation surface
- Deep relationship visualization for entity links
- Changing the publish governance model beyond removing the legacy dataset gate

## Further Notes

This PRD deliberately separates three concerns:

1. Semantic ownership of the Entity
2. Source preparation in Data Studio
3. Lineage visualization in Entity Manager

The current product should feel like an Entity authoring surface with lineage
context, not like a dataset editor with Entity labels.

