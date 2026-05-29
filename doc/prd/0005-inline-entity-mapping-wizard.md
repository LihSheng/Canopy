# PRD: Inline Entity Mapping Wizard (Semantic Layer Config)

Status: draft

## Problem Statement

Dataset Workspace exposes dataset preview and basic dataset operations, but has no way to define a reusable semantic configuration that turns flat columns into a tenant-level Object Type with a primary key and human-readable properties.

Without this, downstream dashboard components cannot rely on consistent, stable “entity” semantics (friendly names, identity, and a curated public field set).

## Solution

Add an **Entity** tab in the Dataset Workspace that hosts an inline, step-based wizard to create/edit a **config-only semantic mapping** for a specific dataset version.

Wizard outputs:

- Tenant-level Object Type selection/creation.
- Dataset-version-scoped primary key selection.
- Column-to-property mappings (rename + include/exclude + optional semantic type).
- Persisted mapping artifact stored in DB, validated on save.

Key constraints:

- UI uses label “Entity”. No “ontology” wording in UI.
- Implementation uses internal naming `semantic_*` to avoid colliding with existing “ontology” modules already in the codebase.
- Mapping is snapshot-scoped to `(dataset_id, dataset_version_id)`.
- No ontology instance hydration in v1 (config-only).

## User Stories

1. As a data studio user, I want an Entity tab on a dataset, so I can discover entity mapping capabilities without leaving the dataset workspace.
2. As a data studio user, I want to see whether the current dataset version already has an entity mapping, so I know if I need to configure it.
3. As a data studio user, I want an empty state with a clear call-to-action when no mapping exists, so I can start configuration quickly.
4. As a data studio user, I want to select an existing Object Type, so multiple datasets can map into the same semantic entity concept.
5. As a data studio user, I want to create a new Object Type inline, so I can model new entities without switching contexts.
6. As a data studio user, I want Object Types to be tenant-scoped, so they are reusable and isolated between tenants.
7. As a data studio user, I want Object Type keys to be unique and stable, so API-facing identifiers remain predictable.
8. As a data studio user, I want Object Type display names to be editable, so UI naming can evolve without breaking identifiers.
9. As a data studio user, I want to define one primary key column for the dataset version, so entity instances are uniquely identifiable.
10. As a data studio user, I want the wizard to block progress if no primary key is selected, so I cannot publish incomplete mappings.
11. As a data studio user, I want the primary key column to be forced-included, so identity is never accidentally excluded.
12. As a data studio user, I want the wizard to show dataset column primitive types, so I can make informed semantic type choices.
13. As a data studio user, I want column primitive types to come from a backend schema source, so UI types are not hardcoded.
14. As a data studio user, I want a semantic type per property (optional), so I can align downstream components with intended meaning.
15. As a data studio user, I want semantic types to default to String, so I can map quickly without perfect typing.
16. As a data studio user, I want to rename technical columns into friendly property names, so dashboards show human-readable labels.
17. As a data studio user, I want auto-suggestions for property names, so I can map faster with less typing.
18. As a data studio user, I want to include or exclude each column, so sensitive/internal columns do not appear downstream.
19. As a data studio user, I want duplicate property names blocked, so the resulting Object Type has unambiguous fields.
20. As a data studio user, I want duplicate property detection to be case-insensitive and whitespace-insensitive, so near-duplicates are blocked correctly.
21. As a data studio user, I want clear inline errors on the exact offending fields, so I can fix issues without guessing.
22. As a data studio user, I want server-side validation to mirror client rules, so invalid mappings cannot be persisted via API.
23. As a data studio user, I want the backend to validate primary key quality on a sample, so obvious null/duplicate key issues are blocked early.
24. As a data studio user, I want mapping saves to be versioned, so edits do not silently overwrite history.
25. As a data studio user, I want to view the existing mapping after publishing, so I can confirm what was saved.
26. As a data studio user, I want to edit an existing mapping for the same dataset version, so I can iterate without creating a new dataset version.
27. As a data studio user, I want edits to create a new mapping version, so previous configurations remain auditable.
28. As a platform operator, I want all mapping APIs to require an active tenant context, so tenant isolation is enforced consistently.
29. As a platform operator, I want mapping storage to live in DB tables, so multi-tenant usage and editability are supported.
30. As a future feature owner, I want mapping output to be representable as YAML/JSON, so it can later drive semantic layer engines.

## Implementation Decisions

- UX naming:
  - UI label is “Entity”.
  - UI must not use “Ontology” wording.
  - Internal naming stays `semantic_*` for now; naming standardization deferred.
- Scope:
  - v1 is config-only mapping (no entity instance hydration).
  - No revamp of the existing ontology module in this iteration.
- Tenancy:
  - Object Types are tenant-scoped and reusable across datasets.
  - All mapping/object-type APIs require an active tenant context.
- Identity:
  - Object Type has a stable `object_type_key` (lowercase snake), unique per tenant, immutable after creation.
  - Object Type has editable `display_name` and optional `description`.
- Snapshot isolation:
  - Mapping is scoped to `(dataset_id, dataset_version_id)`.
  - Mapping edits create a new mapping version record (monotonic `version_number`).
- Validation:
  - Property names are normalized by `trim + case-fold` for uniqueness.
  - Primary key must be selected and must be included.
  - Backend performs sample-based PK validation (block on null/duplicate in sample).
- Column schema typing:
  - UI must not hardcode primitive types.
  - Backend provides dataset version schema with primitive types.
  - Schema source uses hybrid strategy:
    - DB-backed datasets: adapter introspection.
    - Static file datasets: sample inference.
- Data model:
  - New DB tables for:
    - tenant-level object types
    - dataset-version-scoped semantic mappings (versioned)
- Interfaces/modules:
  - Backend “semantic mapping” service layer with pure validation seams.
  - Repository layer for object types and mappings.
  - API layer routes for schema, object types, and mappings.
  - Frontend Entity tab + wizard component(s) + API client methods.

## Testing Decisions

Good tests:

- Assert external behavior (API contracts, validation outcomes, persistence), not internal implementation details.
- Keep validation logic testable as pure functions where possible.
- Prefer service-level tests that cover the full validation + persistence flow.

Modules to test:

- Semantic mapping validation (pure):
  - PK required
  - PK must be included
  - property name normalization and uniqueness
  - schema-column existence checks
- PK sample validator (service/pure seam):
  - null in sample blocks
  - duplicate in sample blocks
- Repository persistence:
  - object type uniqueness per tenant
  - mapping version increments per dataset_version
- API contracts:
  - list/create object types requires tenant context
  - get schema returns primitive types (no hardcoding)
  - create/edit mapping returns validation errors with field context

Prior art:

- Use existing backend unit/integration test patterns already present for API routes, service validation, and repository persistence.
- Use existing frontend unit/integration test patterns for dataset workspace views and inline validation.

## Out of Scope

- Entity instance hydration/materialization into existing ontology storage.
- Relationship/joins mapping between Object Types.
- Full-dataset strict primary key scan (beyond sample-based validation).
- Lineage graph edge creation for entity mappings.
- Naming convergence between `semantic_*` and UI “Entity” (tracked separately).

## Further Notes

- Naming standardization tracked in the semantic-vs-entity TODO note.
- If later convergence into “ontology” is desired, plan a deliberate migration path (API/table renames + UI wording alignment).
