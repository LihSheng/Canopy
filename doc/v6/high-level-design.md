# High-Level Design: Data Connection Workbench

## Overview

This task turns the existing connection/dataset/run workspace into a usable data connection workbench.

The first release is centered on:

- importing static files
- cleaning imported data deterministically
- preserving lineage across re-imports
- showing read-only visualization inside the dataset workspace

The source catalog includes two source types for now:

- `Static File` as the first working path
- `MySQL` as the next source type, visible in the catalog but not required to be fully working in the first slice

## Design Principles

- Keep the workbench read-only with respect to source systems.
- Make every import reproducible and versioned.
- Keep cleaning deterministic and explainable.
- Keep visualization tied to the cleaned dataset version.
- Keep the dataset workspace as the main return point for users.

## Major Modules

### 1. Source Catalog Module

Responsibilities:

- show available source types
- distinguish enabled and future source types
- expose `Static File` and `MySQL`
- route `Static File` into the import/setup flow

### 2. Connection Setup Module

Responsibilities:

- create and store connection records
- store source-specific setup metadata
- accept uploaded static files
- capture source object details needed for lineage

### 3. Import Orchestration Module

Responsibilities:

- coordinate upload, parsing, cleaning, and version creation
- create a run record for each import attempt
- ensure re-imports create a new version instead of overwriting the old one

### 4. Cleaning and Dataset Version Module

Responsibilities:

- apply deterministic cleaning rules
- produce the cleaned dataset artifact
- store immutable dataset versions
- mark the active version for the dataset

### 5. Lineage Module

Responsibilities:

- connect uploaded source object, connection, dataset, version, and run
- expose the lineage graph for the dataset workspace
- keep lineage understandable to users

### 6. Dataset Workspace Visualization Module

Responsibilities:

- show a read-only preview table
- show summary cards for the cleaned dataset
- render a small, deterministic set of charts
- keep the visualization inside the dataset workspace instead of a separate analytics page

### 7. MySQL Readiness Module

Responsibilities:

- keep `MySQL` visible in the source catalog
- keep the domain model compatible with future MySQL import work
- avoid building a separate MySQL-specific workspace

## Data Flow

1. User opens the source catalog.
2. User selects `Static File`.
3. User uploads a file.
4. System captures the raw import and profiles the source object.
5. User selects the source object to turn into a dataset.
6. System runs deterministic cleaning.
7. System stores a new dataset version.
8. System updates lineage and active version state.
9. User opens the dataset workspace.
10. User inspects preview, summary cards, charts, lineage, and version history.
11. On re-import, the same flow creates a new immutable version.

## Interfaces

### Backend Interfaces

- source type listing
- connection creation and preview upload
- dataset creation and listing
- dataset preview and health reads
- dataset version listing
- lineage read
- run history read

### Frontend Interfaces

- source catalog page
- connection setup page
- dataset workspace page
- dataset preview grid
- summary cards and charts
- lineage view
- version selector/history

## Cross-Cutting Concerns

### Determinism

Cleaning and visualization should produce the same output for the same cleaned dataset version.

### Version Safety

Imports must not overwrite previous dataset versions.

### Read-Only Behavior

The workbench must inspect data, not edit source systems.

### Traceability

Every visible dataset result should be traceable back to a source upload.

## Main Tradeoffs

- Keeping MySQL visible but not fully working in the first slice reduces scope risk.
- Keeping visualization inside the dataset workspace avoids creating a second product surface too early.
- Treating re-imports as version creation preserves lineage, but adds a little complexity to the import flow.

## Deferred Items

- full MySQL import implementation
- generic connector framework
- alerts and monitoring
- cross-dataset analytics
- executive dashboard expansion
- write-back or upstream actions
