# V4 Detailed Design: Data Connection Workspace

## Purpose

This document defines the implementation-ready shape for v4 after v3 is
complete.

V4 moves ingestion from an upload-centric workflow to a
connection/dataset/run-centric workspace.

## Core domain model

### Project

Fields:

- `id`
- `name`
- `description`
- `created_at`
- `updated_at`

### SourceType

Fields:

- `id`
- `key`
- `label`
- `category`
- `enabled`
- `tags`
- `description`

Initial source types:

- `static_file` enabled
- `mysql` disabled
- `postgresql` disabled
- `rest_api` disabled
- `google_sheets` disabled
- `csv` disabled

### Connection

Fields:

- `id`
- `project_id`
- `source_type`
- `name`
- `status`
- `config_json`
- `created_at`
- `updated_at`

Excel upload is modeled as `source_type = static_file`.

### Dataset

Fields:

- `id`
- `project_id`
- `connection_id`
- `name`
- `source_object_name`
- `status`
- `active_version_id`
- `created_at`
- `updated_at`

For Excel, each selected sheet becomes one dataset.

### DatasetVersion

Fields:

- `id`
- `dataset_id`
- `run_id`
- `version_number`
- `status`
- `row_count`
- `column_count`
- `storage_path`
- `created_at`

Versions are immutable.

### Run

Fields:

- `id`
- `project_id`
- `connection_id`
- `dataset_id`
- `status`
- `started_by`
- `started_at`
- `finished_at`
- `duration_ms`
- `warning_count`
- `error_message`

### DatasetHealth

Fields:

- `dataset_id`
- `row_count`
- `column_count`
- `missing_required_mappings`
- `warning_count`
- `last_run_status`
- `last_published_version`
- `freshness_at`

## Main screens

### Data Connection Home

Shows:

- new source action
- setup cards
- recent datasets
- recent runs
- project context

### Source Catalog

Shows:

- searchable source cards
- enabled and disabled states
- source tags
- coming-soon detail panel

### Connection Setup

For `static_file`:

- file upload
- workbook detection
- sheet selection
- dataset creation

### Dataset List

Shows:

- dataset name
- source type
- project
- status
- last run
- health summary

### Dataset Workspace

Tabs:

- `Preview`
- `Schema`
- `Transform`
- `Lineage`
- `Runs`
- `Details`

### Run Detail

Shows:

- status
- progress
- duration
- warnings
- output version
- lineage link

## API groups

Suggested route groups:

- `/api/v4/projects`
- `/api/v4/source-types`
- `/api/v4/connections`
- `/api/v4/datasets`
- `/api/v4/datasets/{id}/versions`
- `/api/v4/datasets/{id}/health`
- `/api/v4/datasets/{id}/preview`
- `/api/v4/datasets/{id}/lineage`
- `/api/v4/runs`
- `/api/v4/runs/{id}`

## Frontend modules

- `data-connection-home`
- `source-catalog`
- `connection-setup`
- `project-explorer`
- `dataset-list`
- `dataset-workspace`
- `dataset-preview-grid`
- `dataset-health-panel`
- `run-progress-panel`
- `run-history`
- `lineage-workspace`

## Library decisions

### Preview grid

Use `glide-data-grid`.

Reason:

- spreadsheet-like preview
- high performance for large previews
- MIT licensed
- customizable through theme and cell renderers

### Lineage graph

Use `@xyflow/react`.

Reason:

- mature graph primitives
- custom nodes and edges
- MIT licensed
- suitable for data lineage views

### Icons

Use `lucide-react`.

Reason:

- simple icon primitives
- ISC licensed
- easy to style with existing Tailwind classes

## Execution constraints

- v4 implementation starts only after v3 is complete.
- v4 docs may be prepared before v3 is done.
- v4 should adapt v3 storage/logic where possible, but its user-facing model is
  connection/dataset/run-centric.

