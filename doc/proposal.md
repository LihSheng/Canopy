# Proposal: Data Connection Workbench

> Task tracking label: v6

## Goal

Build a dataset workbench that lets a user import source data, clean it deterministically, preserve lineage across re-imports, and inspect the cleaned result through read-only visualization inside the dataset workspace.

The first usable slice must support static file import end-to-end. The source catalog should also show MySQL as the second source type, but its working import path can follow after the static-file flow is stable.

## Background

The current product already has a connection/dataset/run workspace shape. This task does not replace that structure. It makes that workspace useful for data connection work by focusing on the first import path, the cleaned dataset version, and the visual inspection surface.

The intended product direction is:

- source catalog with two source types only for now
- static file as the first working import path
- MySQL as the next supported source type
- deterministic cleaning before visualization
- lineage recorded from source object to connection, dataset, version, and run
- visualization embedded in the dataset workspace

## Scope

This task includes:

- source catalog with `Static File` and `MySQL`
- static file upload and import flow
- raw import capture
- deterministic cleaning pipeline
- immutable dataset versioning on every re-import
- lineage tracking for imported data
- app-owned connection deletion with dependency checks
- dataset workspace with read-only visualization
- summary cards and preview table for cleaned data
- basic charts derived from cleaned data

## Non-goals

This task does not include:

- executive dashboard redesign
- alerts or monitoring
- cross-dataset analytics
- write-back to source systems
- permissions overhaul
- a generic connector framework
- AI-generated charts or visualizations
- operational actions against upstream systems
- a full MySQL import implementation in the first slice

## Inputs

- uploaded static files
- source metadata captured with the connection
- future MySQL connection metadata, once that connector work starts

## Outputs

- cleaned dataset versions
- dataset preview table
- dataset summary cards
- simple charts from cleaned data
- lineage view for the imported dataset
- version history for re-imports

## Functional Requirements

### Source Catalog

- The source catalog shows only two source types for this task: `Static File` and `MySQL`.
- `Static File` is the active import path.
- `MySQL` is visible in the catalog and aligned to the same model, but its import path can follow after the static-file slice.

### Static File Import

- A user can upload a static file from the dataset workspace flow.
- The system stores the raw import before cleaning.
- The system creates a cleaned dataset version from the imported data.
- The system records a new immutable version on every re-import.

### Cleaning

- The cleaning pipeline is deterministic.
- It trims whitespace, normalizes headers, infers basic types, removes fully empty rows, and flags invalid cells.
- The cleaning pipeline does not use AI.
- The cleaning pipeline does not apply business-rule enrichment in this task.

### Lineage

- Lineage starts at the uploaded source object.
- Lineage links the source object to the connection, dataset, version, and run.
- Users can inspect lineage from the dataset workspace.

### Visualization

- Visualization lives inside the dataset workspace.
- The workspace shows a read-only preview table for cleaned data.
- The workspace shows summary cards for key dataset facts.
- The workspace shows a small set of deterministic charts from cleaned data.
- The workspace does not expose editing of cell values.

### Versioning

- Every re-import creates a new dataset version.
- Previous versions remain accessible for inspection.
- The current active version is explicit in the workspace.

### Connection Deletion

- A user can delete an app-owned connection record when it has no active downstream dependencies.
- The system blocks deletion when the connection is still referenced by active datasets, runs, or other modeled downstream assets.
- Deletion applies to the Canopy Intelligence record only, not the upstream source system.

## Non-Functional Requirements

- Read-only source behavior must be preserved.
- Cleaning and visualization must be deterministic.
- The user should be able to trace every visible dataset result back to a source import.
- The workspace should stay narrow and understandable for the first release.
- The solution should be structured so MySQL can reuse the same dataset and lineage model later.

## Acceptance Criteria

- A user can import a static file successfully.
- The system creates a cleaned dataset version from that import.
- The user can view lineage for that version.
- The user can view read-only visualization inside the dataset workspace.
- A re-import creates a new version instead of overwriting the old one.
- MySQL is visible in the source catalog and fits the same model, even if its working import path is not part of the first slice.
- An unused connection can be deleted, and a used connection is blocked with a dependency message.

## Open Questions Resolved

- Visualization belongs inside the dataset workspace, not a separate analytics page.
- Static file is the first working import path.
- MySQL is the second source type and should stay model-compatible.
- The first task slice should stay focused on import, cleaning, lineage, and visualization rather than broader analytics features.
