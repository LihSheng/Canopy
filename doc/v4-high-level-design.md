# V4 High-Level Design: Connection, Dataset, and Run Workspace

## Overview

V4 redesigns ingestion around durable data assets.

Instead of centering the product on one upload flow, v4 introduces a broader
workspace model:

- projects contain connections, datasets, and runs
- connections produce datasets
- datasets have immutable versions
- runs create or update dataset versions
- lineage explains how versions were produced

V4 should begin after v3 is complete.

## Major modules

### 1. Project Module

Groups connections, datasets, and runs.

Responsibilities:

- create and list projects
- provide default project context
- scope workspace navigation

### 2. Source Catalog Module

Shows available and future source types.

Responsibilities:

- list source types
- expose enabled/disabled state
- route enabled sources into connection setup
- show future-source information panels

### 3. Connection Module

Represents a configured source.

Responsibilities:

- create `static_file` Excel connections
- later support database/API connections
- store source metadata
- own source-specific setup state

### 4. Dataset Module

Represents reusable data assets produced by connections.

Responsibilities:

- create datasets from selected sheets/tables
- list datasets by project
- expose dataset detail workspace
- track active dataset version

### 5. Dataset Version Module

Stores immutable outputs from runs.

Responsibilities:

- preserve version history
- identify active/published version
- connect versions to runs and lineage

### 6. Run Module

Tracks ingestion and processing executions.

Responsibilities:

- create runs
- track current progress
- store run history
- expose run details and warnings

### 7. Dataset Health Module

Summarizes whether a dataset is usable.

Responsibilities:

- compute row/column counts
- summarize warning state
- surface last run and freshness
- flag missing required mappings

### 8. Preview Grid Module

Provides read-only dataset preview.

Responsibilities:

- render large tabular previews
- support column scanning
- keep cell values read-only

### 9. Lineage Module

Connects sources, connections, datasets, versions, and runs.

Responsibilities:

- generate graph nodes and edges
- expose dataset lineage
- support future transform-step expansion

## Data flow

1. User opens a project.
2. User selects `New source`.
3. User chooses `Excel / Static file`.
4. System creates a `Connection`.
5. User uploads workbook.
6. System detects sheets.
7. User selects sheets to create datasets.
8. System creates one dataset per selected sheet.
9. User opens a dataset workspace.
10. User previews, transforms, runs, reviews health, and publishes versions.

## Design tradeoffs

### Why connection/dataset/run now

The current v3 upload model is enough for Excel, but it does not scale cleanly
to MySQL, API, and multi-table sources.

V4 changes the product model before adding those integrations.

### Why dataset-first

Users return to datasets, not upload IDs.
Dataset-first navigation also makes preview, schema, transform, lineage, and
runs easier to understand.

### Why read-only preview

Direct cell editing weakens lineage and reproducibility.
V4 keeps edits in mapping and transform rules.

## Deferred items

- MySQL implementation
- full build tracker
- advanced monitors
- project permissions
- direct cell edits

