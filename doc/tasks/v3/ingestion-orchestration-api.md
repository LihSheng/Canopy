# Ingestion Orchestration And API

## Goal

Orchestrate the end-to-end workflow from upload to preview, cleaning, lineage,
and publish through thin API endpoints and a deterministic backend flow.

## Tasks

- [ ] Define the ingestion workflow state machine.
- [ ] Expose API routes for upload, preview, mapping, processing, lineage, and
  publish.
- [ ] Wire the backend services in the correct order.
- [ ] Persist workflow state transitions explicitly.
- [ ] Keep API handlers thin and business rules in services.
- [ ] Add failure handling that preserves prior immutable artifacts.

## Testing

- [ ] Add integration tests for the upload-to-preview flow.
- [ ] Add integration tests for the process-to-publish flow.
- [ ] Add route tests for each ingestion endpoint.

