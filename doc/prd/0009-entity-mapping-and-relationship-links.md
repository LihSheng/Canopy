# PRD: Entity Mapping and Relationship Links

Status: draft

## Problem Statement

Data Studio can already connect sources, import tables, version datasets, and
show the workbench surface. What it does not yet provide is a reusable semantic
layer for defining tenant-level business objects and their relationships.

Without that layer, each dataset stays a flat technical artifact. Users cannot
declare which dataset columns represent a stable business entity, which column
is the identity key, which fields should be exposed as public properties, or
how one entity should link to another tenant entity.

That creates three product gaps:

- downstream screens cannot rely on stable business meaning
- relationship traversal stays manual or implicit instead of configured
- future ontology-style behavior has no safe config-first foundation

The platform needs a config-only entity layer before any runtime entity
hydration or ontology instance materialization is attempted.

## Solution

Add an Entity mapping flow inside Data Studio / Dataset Workspace that lets a
user define a reusable semantic object type for a dataset version and attach
relationship links to other tenant entities.

The flow should:

- let a user create or select a tenant-scoped Object Type
- let a user choose one primary key column for the dataset version
- let a user rename technical columns into curated property names
- let a user include or exclude columns from the public semantic surface
- let a user optionally assign semantic types to properties
- let a user declare relationship links to existing tenant Object Types
- persist the mapping as a versioned artifact scoped to the dataset version
- validate all mapping and link rules before save

This is config-only in v1:

- no entity instance hydration
- no ontology storage revamp
- no executable join generation from links
- no downstream write-back

## User Stories

1. As a data studio user, I want an Entity tab on a dataset, so that I can
   define business meaning without leaving the workspace.
2. As a data studio user, I want to create a new Object Type inline, so that I
   can model a new semantic concept quickly.
3. As a data studio user, I want to select an existing Object Type, so that I
   can reuse a tenant entity that already exists.
4. As a data studio user, I want the Object Type key to be stable, so that API
   identifiers remain predictable over time.
5. As a data studio user, I want the Object Type display name to be editable,
   so that the UI can evolve without breaking storage identifiers.
6. As a data studio user, I want to see dataset column primitive types, so that
   I can choose property semantics with context.
7. As a data studio user, I want a single primary key column per dataset
   version, so that entity identity stays explicit.
8. As a data studio user, I want the wizard to block progress if no primary key
   is selected, so that incomplete mappings cannot be saved.
9. As a data studio user, I want the primary key column to be forced included,
   so that identity is never accidentally excluded.
10. As a data studio user, I want to rename technical columns into friendly
    property names, so that downstream users see readable labels.
11. As a data studio user, I want to include or exclude each column, so that
    sensitive or internal fields do not leak downstream.
12. As a data studio user, I want semantic types to be optional, so that I can
    configure quickly without perfect typing.
13. As a data studio user, I want semantic types to default sensibly, so that
    the wizard is fast for common cases.
14. As a data studio user, I want duplicate property names blocked, so that the
    resulting Object Type stays unambiguous.
15. As a data studio user, I want duplicate property checks to ignore case and
    extra whitespace, so that near-duplicates are rejected correctly.
16. As a data studio user, I want inline validation messages on the exact bad
    field, so that I can fix mistakes without guessing.
17. As a data studio user, I want server validation to match client validation,
    so that invalid mappings cannot slip through the API.
18. As a data studio user, I want mapping saves to be versioned, so that edits
    never silently overwrite history.
19. As a data studio user, I want to view the current mapping after publish, so
    that I can confirm what was saved.
20. As a data studio user, I want to edit an existing mapping for the same
    dataset version, so that I can refine the config without creating a new
    dataset version.
21. As a data studio user, I want edits to create a new mapping version, so
    that previous configurations remain auditable.
22. As a data studio user, I want an additional step for relationship links, so
    that I can connect this entity to other tenant entities in one flow.
23. As a data studio user, I want to choose a source property from my mapped
    properties, so that each link is based on curated semantic data.
24. As a data studio user, I want to select a target Object Type, so that I can
    connect to another tenant entity.
25. As a data studio user, I want the target key to resolve to the target
    Object Type's primary key, so that relationship identity stays stable.
26. As a data studio user, I want relationship cardinality options, so that the
    traversal intent is explicit.
27. As a data studio user, I want duplicate link IDs blocked, so that link
    references stay unique.
28. As a data studio user, I want duplicate edges blocked, so that I do not
    create redundant or conflicting relationships.
29. As a data studio user, I want links to be blocked when the source property
    is excluded, so that private fields cannot leak through relationships.
30. As a data studio user, I want incompatible link key types blocked, so that
    I do not save broken relationships.
31. As a platform operator, I want all mapping APIs to require tenant context,
    so that entity definitions stay tenant-scoped.
32. As a platform operator, I want mapping data to live in database tables, so
    that the configuration is durable and editable.
33. As a future feature owner, I want the output to be representable as JSON or
    YAML, so that a later semantic engine can consume it.
34. As a future feature owner, I want the relationship metadata to stay
    extensible, so that bridge or junction modeling can be added later.

## Implementation Decisions

- The feature is semantic/entity config only.
- UI naming uses `Entity`, not `Ontology`.
- Internal naming stays `semantic_*` for now.
- The mapping is scoped to `(dataset_id, dataset_version_id)`.
- Object Types are tenant-scoped and reusable across datasets.
- Mapping edits create a new versioned record instead of overwriting history.
- The mapping captures:
  - one required primary key
  - include/exclude flags for properties
  - optional semantic type per property
  - friendly property names
  - optional relationship links
- Link declarations are stored with the same mapping version as the property
  configuration.
- Target Object Type selection is tenant-wide, not dataset-local.
- Target key resolution uses the target Object Type's latest published mapping
  primary key in v1.
- Validation must cover:
  - required primary key
  - primary key inclusion
  - property-name uniqueness after trim and case-fold
  - schema-column existence
  - duplicate link IDs
  - duplicate edges
  - excluded-source-property blocking
  - link key type compatibility
- Backend modules should be split into small, testable units:
  - semantic mapping validation
  - object type repository
  - mapping repository
  - PK sample validation
  - link validation
  - schema discovery / dataset schema source
- API surface should support:
  - schema reads for dataset versions
  - object type list/create/update
  - mapping get/create/update/validate
  - link payload read/write inside mapping contracts
- Frontend should expose:
  - Entity tab in dataset workspace
  - step-based mapping wizard
  - relationship link editor inside the wizard flow
  - inline validation and save feedback
- No runtime hydration or ontology instance writes should be introduced in this
  slice.

## Testing Decisions

- Good tests verify external behavior, not implementation details.
- Validation logic should be covered with pure tests wherever possible.
- Repository and API contracts should be covered with integration tests.
- Frontend should have component and page-flow tests for the wizard and link
  editor.
- Modules to test:
  - primary key validation
  - property normalization and duplicate detection
  - sample-based PK quality checks
  - object type persistence and uniqueness
  - mapping version increments
  - link validation rules
  - mapping API create/update/get/validate behavior
  - Entity wizard step flow
  - relationship link editor behavior
- Prior art:
  - existing backend unit tests for validation-heavy modules
  - existing backend integration tests for API and persistence flows
  - existing frontend unit tests for wizard and editor components

## Out of Scope

- Entity instance hydration or runtime materialization
- Legacy ontology storage redesign
- Executable joins generated from relationship links
- Cross-dataset query planning
- Many-to-many junction modeling beyond metadata declaration
- Cross-tenant relationships
- Full semantic layer engine integration
- Dashboard write-back actions

## Further Notes

This PRD is the semantic foundation for the next product step after Data
Studio.

The intended progression is:

1. Data Studio connection and dataset workbench
2. Entity mapping and relationship declarations
3. Later ontology or semantic-layer consumption, if and when that is promoted
   from config-only to runtime behavior

The repo already uses the term `Entity` for the UI and `semantic_*` for the
implementation layer. Keep that split until a deliberate naming migration is
approved.
