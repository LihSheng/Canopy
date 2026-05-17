# V3 To V4 Migration Layer

## Goal

Adapt completed v3 ingestion data to the v4 connection/dataset/run model
without breaking existing behavior.

## Tasks

- [ ] Map v3 uploads to `static_file` connections.
- [ ] Map selected sheets to datasets.
- [ ] Map cleaned snapshots to dataset versions.
- [ ] Map processing events to runs.
- [ ] Preserve v3 lineage while exposing v4 graph nodes.

## Testing

- [ ] Add migration/read-adapter tests for existing v3 records.
- [ ] Add regression tests for v3 APIs if they remain available.

