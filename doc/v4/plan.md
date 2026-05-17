# V4 Plan

## Purpose

This document is the planning entrypoint for v4.

V4 is a Data Connection Workspace redesign that should start after v3 is
complete. V3 finishes the Excel ingestion pipeline. V4 turns that capability
into a broader connection, dataset, run, and project workspace that can support
future source integrations.

## Baseline

V3 is upload-centric:

- Excel upload
- workbook preview
- mapping review
- cleaning templates
- column-level lineage
- publish flow

V4 should move the product model to:

- `Project`
- `SourceType`
- `Connection`
- `Dataset`
- `DatasetVersion`
- `Run`
- `LineageGraph`

## V4 scope

V4 delivers:

- Data Connection home launchpad
- project/folder context
- source catalog with enabled and future source types
- `static_file` connection model for Excel
- one connection creating multiple datasets
- user-selected Excel sheets as datasets
- dataset-first workspace
- read-only dataset preview grid
- simple Dataset Health panel
- run progress and run history
- lineage entry from dataset workspace

V4 does not deliver:

- MySQL implementation
- advanced permissions
- direct cell editing
- full cross-dataset build tracker
- full monitoring/alerting
- source-system write-back

## Confirmed requirements

- V4 is docs/tasks first and should proceed only after v3 is complete.
- Backend concepts should change from `upload-centric` to
  `connection/dataset/run-centric`.
- Excel upload is modeled as a `Connection` with source type `static_file`.
- One connection can create multiple datasets.
- For Excel, the user selects which sheets become datasets.
- Connections, datasets, and runs belong to a `Project`.
- V4 is dataset-first: templates and transforms live inside the dataset
  workspace.
- Dataset preview is read-only.
- V4 includes current run progress and lightweight run history.
- V4 includes a simple Dataset Health panel.
- Source catalog shows future source types as disabled cards.

## Recommended third-party libraries

Use third-party libraries only where they provide difficult primitives without
owning the whole product model.

Recommended:

- `glide-data-grid` for the dataset preview grid
- `@xyflow/react` for lineage graph rendering
- `lucide-react` for icons

Avoid for first v4 pass:

- `AG Grid` unless the preview grid needs heavier enterprise behavior
- `@tanstack/react-table` unless dependency security has been reviewed and
  versions are pinned

## Required v4 planning questions before implementation

1. What is the minimum `Project` model?
2. Which source catalog cards are visible on day one?
3. What dataset tabs are included in the first v4 implementation?
4. What Dataset Health fields are blocking versus informational?
5. Which v3 APIs can be adapted versus replaced by v4 APIs?

## Architecture guardrails

V4 must preserve:

- read-only source behavior
- immutable dataset versions
- deterministic processing
- first-class lineage
- v3 completion before v4 implementation
- clear separation between source configuration, dataset assets, and run
  execution

