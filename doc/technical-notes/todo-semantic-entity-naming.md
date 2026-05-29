# TODO: Semantic vs Entity Naming Standardization

We are introducing an “Entity” UI surface for semantic mapping configuration inside the Dataset Workspace.

Implementation uses internal `semantic_*` naming to avoid collision/confusion with existing backend `apps/backend/ontology/*` modules.

## TODO

- Decide canonical product term:
  - UI: Entity (current)
  - Internal: semantic (current)
  - Existing module: ontology (already used for snapshot-scoped normalized business objects)
- Standardize naming across:
  - backend module/package names
  - DB table names
  - API route prefixes
  - frontend component names + tab labels
- Decide deprecation/migration path if we converge semantic mapping config into ontology later.

