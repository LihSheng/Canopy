# Ingestion Orchestration And API

## Goal

Orchestrate the end-to-end workflow from upload to preview, cleaning, lineage,
and publish through thin API endpoints and a deterministic backend flow.

## Tasks

- [x] Define the ingestion workflow state machine.
- [x] Expose API routes for upload, preview, mapping, processing, lineage, and
  publish.
- [x] Wire the backend services in the correct order.
- [x] Persist workflow state transitions explicitly.
- [x] Keep API handlers thin and business rules in services.
- [x] Add failure handling that preserves prior immutable artifacts.

## Testing

- [x] Add integration tests for the upload-to-preview flow.
- [x] Add integration tests for the process-to-publish flow.
- [x] Add route tests for each ingestion endpoint.

