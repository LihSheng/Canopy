# Issues: Entity Relationship Link Declarations (vertical slices)

Status: draft

1) **Mapping API accepts `links[]` + validate**
- Type: AFK
- Blocked by: None
- What to build: Extend semantic mapping API request/response + validate endpoint to accept/return `links[]`. Add backend validation for `link_id` required, duplicate `link_id`, duplicate edge, excluded source property, and type compatibility (source vs target PK).
- Acceptance criteria:
  - [ ] `GET mapping` returns `links[]` when present
  - [ ] `POST/PUT mapping` persists `links[]`
  - [ ] `/validate` returns field-scoped link errors with clear messages

2) **Target PK resolution for link validation**
- Type: AFK
- Blocked by: Slice 1
- What to build: Backend resolves “target PK” by looking up the latest mapping for `target_object_type_id` (tenant-scoped), then uses its `is_primary_key=true` property for type checks.
- Acceptance criteria:
  - [ ] Missing target mapping or missing target PK returns clear validation error
  - [ ] Type mismatch returns “Key Compatibility Error …” style message

3) **Wizard UI step: Links (basic CRUD)**
- Type: AFK
- Blocked by: Slice 1
- What to build: Add Step 4 “Relationships/Links” in Entity mapping wizard. UI supports list/add/edit/remove links with fields: `link_id`, `display_name`, `source_property_key`, `target_object_type_id`, `cardinality`. Target key is shown as read-only resolved PK (v1). Cardinality options in v1: `many_to_one`, `many_to_many`.
- Acceptance criteria:
  - [ ] Users can add/edit/remove link rows before publish
  - [ ] UI blocks save on backend validation errors with inline field markers

4) **Many-to-many UX + warnings (metadata-only)**
- Type: AFK
- Blocked by: Slice 3
- What to build: Allow selecting `many_to_many` cardinality. Show inline warning that v1 is metadata-only (no junction config/executable join yet).
- Acceptance criteria:
  - [ ] `many_to_many` selectable and persists
  - [ ] Warning visible and non-blocking

5) **Regression tests (unit + integration)**
- Type: AFK
- Blocked by: Slice 1, Slice 2
- What to build: Add unit tests for link validation rules and integration tests for mapping create/update/validate with links.
- Acceptance criteria:
  - [ ] New tests cover duplicates, excluded source, type mismatch, missing target PK
  - [ ] Existing semantic tests still pass
