# TODO: Entity Epic Split

We are keeping the next semantic step dataset-centric for now.

## Locked scope

- Primary UI stays inside Dataset Workspace as an `Entity` tab.
- The first epic covers dataset-level Entity mapping only.
- Object Types remain tenant-scoped and reusable across datasets.
- There is no central Object Type registry page in this phase.

## Epic 1: Dataset Entity Mapping

- Show current Entity mapping state for a dataset version.
- Let the user create or select an Object Type inline.
- Let the user pick one primary key column.
- Let the user rename columns into curated property names.
- Let the user include or exclude properties.
- Let the user assign semantic types.
- Save the mapping as a versioned record.

## Epic 2: Relationship Links

- Add relationship links after base mapping works.
- Let the user select a source property from mapped properties.
- Let the user select a target Object Type.
- Resolve the target key from the target Object Type's primary key.
- Support `many_to_one` and `many_to_many` metadata-only links.
- Keep link validation and versioning aligned with the base mapping artifact.

## Deferred

- Central entity management / registry page.
- Multi-table entity composer.
- Runtime entity hydration.
- Executable joins from links.
- Ontology storage redesign.

