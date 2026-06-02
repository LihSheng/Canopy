# PRD: Dataset Entity Mapping

Status: draft

## Problem Statement

Data Studio can already connect sources, import data, version datasets, and
present the dataset workspace. What it does not yet provide is a stable,
dataset-scoped way to describe what business object a cleaned dataset version
represents.

Without that layer, each dataset version remains a technical artifact only.
Users cannot consistently say "this dataset version is an Employee entity" or
"these columns form the business object identity and public surface".

That creates three product gaps:

- downstream product surfaces cannot rely on a reusable business object model
- dataset configurations remain hard to interpret outside the original author
- future semantic behavior has no clean config-first foundation to build on

The platform needs a config-only Entity mapping layer before any relationship
linking or runtime semantic hydration is attempted.

## Solution

Add an Entity tab inside the Dataset Workspace that lets a user define the
Entity for a specific dataset version.

The flow should:

- let a user create or select a tenant-scoped Object Type inline
- let a user choose one primary key column for the dataset version
- let a user rename technical columns into curated property names
- let a user include or exclude columns from the public semantic surface
- let a user optionally assign semantic types to properties
- let a user save the mapping as a versioned artifact scoped to the dataset
  version
- let a user view and edit the current mapping for the same dataset version
- validate mapping rules before save

This is config-only:

- no relationship links in this slice
- no entity instance hydration
- no ontology storage revamp
- no executable join generation
- no downstream write-back

## User Stories

1. As a data studio user, I want an Entity tab on a dataset, so that I can
   define business meaning without leaving the workspace.
2. As a data studio user, I want to see whether the current dataset version
   already has an Entity mapping, so that I know if I need to configure it.
3. As a data studio user, I want to create a new Object Type inline, so that I
   can model a new semantic concept quickly.
4. As a data studio user, I want to select an existing Object Type, so that I
   can reuse a tenant entity that already exists.
5. As a data studio user, I want the Object Type key to be stable, so that API
   identifiers remain predictable over time.
6. As a data studio user, I want the Object Type display name to be editable,
   so that the UI can evolve without breaking storage identifiers.
7. As a data studio user, I want to know which dataset version the Entity maps
   to, so that the scope of the configuration is obvious.
8. As a data studio user, I want to see dataset column primitive types, so that
   I can choose property semantics with context.
9. As a data studio user, I want a single primary key column per dataset
   version, so that entity identity stays explicit.
10. As a data studio user, I want the wizard to block progress if no primary
    key is selected, so that incomplete mappings cannot be saved.
11. As a data studio user, I want the primary key column to be forced
    included, so that identity is never accidentally excluded.
12. As a data studio user, I want to rename technical columns into friendly
    property names, so that downstream users see readable labels.
13. As a data studio user, I want to include or exclude each column, so that
    sensitive or internal fields do not leak downstream.
14. As a data studio user, I want semantic types to be optional, so that I can
    configure quickly without perfect typing.
15. As a data studio user, I want semantic types to default sensibly, so that
    the wizard is fast for common cases.
16. As a data studio user, I want duplicate property names blocked, so that the
    resulting Object Type stays unambiguous.
17. As a data studio user, I want duplicate property checks to ignore case and
    extra whitespace, so that near-duplicates are rejected correctly.
18. As a data studio user, I want inline validation messages on the exact bad
    field, so that I can fix mistakes without guessing.
19. As a data studio user, I want server validation to match client validation,
    so that invalid mappings cannot slip through the API.
20. As a data studio user, I want mapping saves to be versioned, so that edits
    never silently overwrite history.
21. As a data studio user, I want to view the current mapping after publish,
    so that I can confirm what was saved.
22. As a data studio user, I want to edit an existing mapping for the same
    dataset version, so that I can refine the config without creating a new
    dataset version.
23. As a data studio user, I want edits to create a new mapping version, so
    that previous configurations remain auditable.
24. As a platform operator, I want all mapping APIs to require tenant context,
    so that entity definitions stay tenant-scoped.
25. As a platform operator, I want mapping data to live in database tables, so
    that the configuration is durable and editable.
26. As a future feature owner, I want the output to be representable as JSON or
    YAML later, so that a later semantic engine can consume it.

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
- The target data source for the Entity is the current dataset version already
  loaded into Data Studio.
- The selected Object Type key is stable and server-owned; the server derives
  the persisted key from the validated Object Type rather than trusting the
  client payload.
- Validation must cover:
  - required primary key
  - primary key inclusion
  - property-name uniqueness after trim and case-fold
  - schema-column existence
  - semantic type allowlist
  - sample-based primary key quality checks when schema is available
  - tenant ownership of the selected Object Type
- Backend modules should be split into small, testable units:
  - semantic mapping validation
  - object type repository
  - mapping repository
  - PK sample validation
  - schema discovery / dataset schema source
- API surface should support:
  - schema reads for dataset versions
  - object type list/create/update
  - mapping get/create/update/validate
- Frontend should expose:
  - Entity tab in dataset workspace
  - step-based mapping wizard
  - inline Object Type selection/creation
  - inline validation and save feedback
- No relationship link declarations should be introduced in this slice.
- No runtime hydration or ontology instance writes should be introduced in this
  slice.

## Testing Decisions

- Good tests verify external behavior, not implementation details.
- Validation logic should be covered with pure tests wherever possible.
- Repository and API contracts should be covered with integration tests.
- Frontend should have component and page-flow tests for the wizard.
- Modules to test:
  - primary key validation
  - property normalization and duplicate detection
  - sample-based PK quality checks
  - object type persistence and uniqueness
  - mapping version increments
  - mapping API create/update/get/validate behavior
  - Entity wizard step flow

Prior art:

- existing backend unit tests for validation-heavy modules
- existing backend integration tests for API and persistence flows
- existing frontend unit tests for wizard and workspace components

## Out of Scope

- Relationship link declarations
- Entity instance hydration or runtime materialization
- Legacy ontology storage redesign
- Executable joins generated from links
- Cross-dataset query planning
- Central entity registry page
- Many-to-many junction modeling
- Cross-tenant entities
- Dashboard write-back actions

## Further Notes

This PRD is the first half of the semantic foundation after Data Studio.

The intended progression is:

1. Data Studio connection and dataset workbench
2. Dataset Entity mapping
3. Relationship link declarations
4. Later semantic-layer or ontology consumption, if and when that is promoted
   from config-only to runtime behavior

Keep the user-facing term `Entity` and the internal implementation term
`semantic_*` until a deliberate naming migration is approved.
