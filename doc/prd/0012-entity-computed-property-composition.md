# PRD: Entity Computed Property Composition

Status: draft

## Problem Statement

The graph-based Entity Designer can already model one source field mapped to
one Entity property, and it can already attach multiple source nodes to the
same Entity.

That works for simple semantic objects. It does not work for real business
objects that need a composed property derived from multiple fields or multiple
sources.

Examples:

- a `full_name` property derived from `first_name` and `last_name`
- a `plant_status` property derived from a raw table plus a static reference
  file
- a `region_label` property derived from a code field and a lookup source

Without computed property composition:

- users must pre-shape data outside the Entity Designer
- the graph cannot express how a business property is assembled
- the Entity model remains too rigid for realistic semantic design

The platform needs a config-only computed property layer on top of the current
Entity graph, without turning the system into a full transform engine.

## Solution

Extend the Entity Designer so a user can define computed Entity properties that
reference multiple source fields and, when needed, multiple source nodes.

The feature should let a user:

- create a computed property inside the Entity graph
- reference more than one source field
- reference source fields from different source nodes
- define a clear expression or composition rule
- preview the resulting property definition before saving
- keep versioned config behavior unchanged

This is still config-only:

- no runtime execution engine
- no ad hoc SQL generation
- no general-purpose ETL designer
- no cross-dataset query planner
- no write-back to source systems

## User Stories

1. As a data studio user, I want to define a computed Entity property, so that
   I can model business meaning that does not exist as a single source column.
2. As a data studio user, I want to combine multiple source fields into one
   property, so that I can express realistic business attributes.
3. As a data studio user, I want to combine fields from different source nodes,
   so that one Entity can be composed from multiple raw inputs.
4. As a data studio user, I want to create a `full_name` property from first
   name and last name fields, so that the Entity surface is business-friendly.
5. As a data studio user, I want to create lookup-based properties from a raw
   table plus a static file, so that I can enrich the Entity with reference
   data.
6. As a data studio user, I want to see which fields feed a computed property,
   so that I can understand how it is assembled.
7. As a data studio user, I want computed properties to appear in the same
   graph-based Entity Designer, so that I do not need a separate transform UI.
8. As a data studio user, I want computed properties to save as versioned
   config, so that I can change business logic without losing history.
9. As a data studio user, I want the graph to validate missing source fields,
   so that I do not save broken property definitions.
10. As a data studio user, I want the graph to prevent duplicate or ambiguous
    computed property names, so that the Entity surface stays unambiguous.
11. As a data studio user, I want to keep simple one-field properties and
    computed properties side by side, so that I can mix basic and advanced
    modeling in one Entity.
12. As a data studio user, I want the computed property editor to live in the
    right-side drawer, so that I can stay in the canvas while editing.
13. As a data studio user, I want to preview the computed property's source
    references before saving, so that I can verify the composition.
14. As a data studio user, I want the computed property logic to be explicit,
    so that other users can understand the model later.
15. As a platform operator, I want computed properties to remain tenant-scoped,
    so that Entity definitions do not leak across tenants.
16. As a platform operator, I want computed properties to live in the same
    versioned mapping record, so that the configuration remains durable.
17. As a future feature owner, I want the composition model to be portable as
    JSON later, so that a later semantic engine can interpret it.
18. As a future feature owner, I want to keep the composition model simple
    enough to evolve into a runtime engine later, so that we do not paint
    ourselves into a corner.

## Implementation Decisions

- The feature is config-only property composition.
- UI naming remains `Entity`.
- The graph remains the primary authoring surface.
- Computed properties are authored in the graph-side drawer.
- A computed property can reference multiple source fields.
- A computed property can reference fields from multiple source nodes.
- The current versioned `Semantic Mapping` record remains the storage unit.
- Simple one-field properties stay supported.
- Computed properties must coexist with ordinary mapped properties.
- Validation must cover:
  - missing source fields
  - duplicate property names
  - ambiguous property references
  - stable property identifiers
  - tenant ownership of the selected Entity context
- The composition model should be explicit, not implicit.
- The saved representation should remain JSON-friendly for a future semantic
  engine.
- The feature should not require a full transform pipeline or new runtime
  executor.

## Testing Decisions

- Good tests verify external behavior, not implementation details.
- Composition rules should be covered with pure tests wherever possible.
- Graph editor behavior should be covered with component and flow tests.
- Backend mapping contracts should be covered with integration tests.
- Modules to test:
  - computed property validation
  - property reference resolution
  - duplicate and ambiguity detection
  - versioned save and reload behavior
  - coexistence of computed and simple properties
- Prior art:
  - existing semantic mapping validation tests
  - existing graph editor component tests
  - existing versioned API integration tests

## Out of Scope

- Runtime evaluation of computed properties
- Generated SQL or ETL job execution
- Cross-dataset joins as an execution engine
- Full transform pipeline authoring
- Source system write-back
- General-purpose scripting inside the Entity Designer
- Multi-tenant graph browsing
- Ontology storage redesign

## Further Notes

This PRD is the next semantic step after the graph-based Entity Designer.

The progression is:

1. Data Studio connection and dataset workbench
2. Graph-based Entity Designer
3. Computed property composition
4. Later runtime semantic consumption, if and when it is promoted from config
   to execution

Keep this feature config-only until a deliberate runtime execution decision is
made.
