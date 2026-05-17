# Cleaning Engine And Normalization

## Goal

Execute published transformation templates against immutable raw snapshots and
produce cleaned, normalized output that can feed ontology publish.

## Tasks

- [ ] Load the selected published template version for execution.
- [ ] Apply cleaning steps deterministically in order.
- [ ] Produce immutable cleaned snapshots.
- [ ] Record warnings and row-level issues.
- [ ] Normalize cleaned rows into canonical business-ready fields.
- [ ] Preserve raw-to-cleaned field lineage references.

## Testing

- [ ] Add unit tests for each supported cleaning step.
- [ ] Add integration tests for cleaned snapshot persistence.
- [ ] Add integration tests for normalization output shape.

