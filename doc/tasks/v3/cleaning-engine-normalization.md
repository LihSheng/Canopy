# Cleaning Engine And Normalization

## Goal

Execute published transformation templates against immutable raw snapshots and
produce cleaned, normalized output that can feed ontology publish.

## Tasks

- [x] Load the selected published template version for execution.
- [x] Apply cleaning steps deterministically in order.
- [x] Produce immutable cleaned snapshots.
- [x] Record warnings and row-level issues.
- [x] Normalize cleaned rows into canonical business-ready fields.
- [x] Preserve raw-to-cleaned field lineage references.

## Testing

- [x] Add unit tests for each supported cleaning step.
- [x] Add integration tests for cleaned snapshot persistence.
- [x] Add integration tests for normalization output shape.

