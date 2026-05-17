# Lineage Graph And Storage

## Goal

Store and render lineage as a first-class graph that can later expand from
column-level lineage to full transformation-step lineage.

## Tasks

- [ ] Define lineage node types for file, workbook, sheet, column, cleaned
  field, and ontology-ready field.
- [ ] Define lineage edge types for derivation and mapping relationships.
- [ ] Persist lineage as first-class DB records.
- [ ] Generate column-level lineage from profiling, mapping, and cleaning.
- [ ] Expose graph data as node and edge arrays.
- [ ] Render a read-only lineage graph in the UI.

## Testing

- [ ] Add unit tests for lineage node and edge generation.
- [ ] Add integration tests for lineage API responses.
- [ ] Add frontend tests for graph rendering and node details.

