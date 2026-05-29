# PRD: Entity Relationship Link Declarations (Semantic Config)

Status: draft

## Problem Statement

Entity mappings currently define an Object Type, a primary key, and property mappings for a dataset version. But entities remain isolated: there is no way to declare relationships (links) between a newly mapped entity and existing tenant entities.

Without explicit links, future semantic traversal (master-detail UI, cross-entity lookup, lineage edges) cannot be configured safely or validated early.

## Solution

Extend the existing Dataset Workspace **Entity** mapping wizard with an additional step to define **Relationship Links** between the current mapped Object Type and other tenant-level Object Types.

Wizard output additions:

- A list of link declarations attached to the dataset-version-scoped mapping artifact.
- Validated link metadata (IDs, source/target properties, cardinality).
- Editable after publish (creates a new mapping version like other edits).

Key constraints:

- UI uses label “Entity” (no “Ontology” wording).
- v1 is config-only (no runtime join execution, no entity hydration).
- Relationship links are stored/versioned with the mapping for `(dataset_id, dataset_version_id)`.

## User Stories

1. As a data studio user, I want to add relationship links while mapping an Entity, so I can connect new data to existing tenant entities in one flow.
2. As a data studio user, I want to see existing links for the current dataset version mapping, so I know what relationships are already configured.
3. As a data studio user, I want to create a new link by selecting a source property from my mapped properties, so the link is based on a curated semantic field.
4. As a data studio user, I want to select a target Object Type from all tenant entities, so I can link to entities created from other datasets.
5. As a data studio user, I want the target key to default to the target entity’s primary key, so the relationship joins on a stable identity.
6. As a data studio user, I want to set relationship cardinality (many-to-one or many-to-many), so downstream traversal can be modeled correctly.
7. As a data studio user, I want duplicate link IDs blocked, so link references remain unambiguous.
8. As a data studio user, I want duplicate edges blocked (same source property to same target object), so I don’t create redundant/conflicting links.
9. As a data studio user, I want links to be blocked if the source property is excluded, so private/internal fields cannot leak via relationships.
10. As a data studio user, I want clear errors when link key types are incompatible, so I can correct mappings before publish.
11. As a platform operator, I want all link APIs to require tenant context, so links cannot cross tenants.
12. As a future feature owner, I want the link metadata format to be extensible, so later support for junction/bridge modeling and executable joins can be added without breaking old configs.

## Implementation Decisions

- UX naming:
  - UI label remains “Entity”.
  - UI and docs for this epic use “Entity Relationship Links” (avoid “Ontology” wording).
  - Internal naming remains `semantic_*` for now.
- Placement:
  - Relationship links appear as an additional step/section inside the existing Entity mapping wizard flow.
- Storage / versioning:
  - Link declarations are stored inside the same dataset-version mapping artifact (same record family/versioning as PK + properties).
  - Editing links creates a new mapping version record.
- Target object set:
  - Target Object Type dropdown is populated from the tenant-level Object Type dictionary (all published object types for the tenant).
- Target primary key resolution:
  - Target key selection is restricted to the target Object Type’s primary key in v1.
  - Since primary key is defined per mapping (dataset-version scoped), “target primary key” resolves to the **latest mapping version** for the selected `target_object_type_id` within the tenant, using its `is_primary_key=true` property.
- Link shape (per link):
  - `link_id`: unique per mapping (normalized by `trim + case-fold` for comparison).
  - `display_name`: user-facing label.
  - `source_property_key`: must reference a property from the current mapping’s properties list.
  - `target_object_type_id`: references an existing tenant object type.
  - `target_property_key`: restricted to the target object type’s primary key in v1.
  - `cardinality`: allowed values in v1 are `many_to_one` and `many_to_many`.
- Many-to-many (v1 meaning):
  - Metadata-only declaration. No junction dataset selection, no bridge modeling, and no executable join guarantees in v1.
  - UI should communicate that it is non-executable until future enhancements.
- Validation (client + server):
  - Block missing/empty `link_id` and `display_name`.
  - Block duplicate `link_id` within a mapping (case-insensitive + trimmed).
  - Block duplicate edge within a mapping: `(source_property_key, target_object_type_id)` duplicates.
  - Block links using excluded source properties.
  - Block incompatible key types between `source_property` semantic type and `target_primary_key` semantic type.

## Testing Decisions

Good tests:

- Assert external behavior (validation errors, persistence, API contracts), not internal implementation details.
- Keep link validation as pure validation functions where possible, tested in isolation.
- Cover both create and update flows for mappings that include links.

Modules to test:

- Link validation:
  - duplicate `link_id`
  - duplicate edges
  - excluded source property blocks
  - type compatibility errors
- Mapping persistence:
  - saving links persists in mapping record
  - editing links increments mapping version
- API contracts:
  - get mapping returns links when present
  - validate endpoint returns link field errors with clear field context

Prior art:

- Follow existing semantic mapping unit tests for validation rules.
- Follow existing semantic API integration tests for create/update/validate flows.

## Out of Scope

- Executable join generation or query planning from link declarations.
- Junction/bridge dataset selection or modeling for many-to-many.
- Linking directly into legacy ontology storage modules.
- Rendering link edges in lineage graph UI.
- Cross-dataset entity instance hydration/merge based on links.

## Further Notes

- Restricting v1 target keys to the target primary key reduces ambiguity and makes future join execution safer.
- Future enhancements can expand target key selection to include other unique/indexed target properties, with backward compatibility.
