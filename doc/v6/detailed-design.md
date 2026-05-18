# Detailed Design: Data Connection Workbench

## Scope Alignment

This design expands the static-file first workbench described in `doc/proposal.md` and `doc/v6/high-level-design.md`.

It is intentionally narrow:

- static file import must work end-to-end
- cleaned dataset versions must be immutable
- lineage must be visible from the dataset workspace
- visualization must live in the dataset workspace
- MySQL must remain model-compatible and visible in the catalog

## Module Design

### 1. Source Catalog Module

#### Responsibilities

- list source types from the source type repository
- expose enabled and disabled states
- show `Static File` as the active path
- show `MySQL` as the next source type

#### Data Structures

- `SourceType`
  - `key`
  - `label`
  - `category`
  - `enabled`
  - `tags`
  - `description`

#### Control Flow

- source type records are seeded once
- the UI filters and displays them as catalog cards
- `Static File` routes into setup
- `MySQL` can render as visible but not fully actionable in the first slice

#### Error Handling

- failed source-type load shows an error state
- missing source-type data falls back to an empty catalog state

#### Tests

- verify source type seeding
- verify enabled and disabled card rendering
- verify search/filter behavior

### 2. Connection Setup Module

#### Responsibilities

- create connection records
- store source metadata in `config_json`
- accept static-file uploads
- keep raw upload metadata for lineage

#### Data Structures

- `ConnectionModel`
  - `project_id`
  - `source_type`
  - `name`
  - `status`
  - `config_json`
  - `created_at`
  - `updated_at`

Recommended `config_json` keys for static-file imports:

- `file_name`
- `source_file_path`
- `selected_sheet_names`
- `source_object_name`
- `import_mode`

#### Control Flow

- user uploads a file through the setup page
- backend stores the upload and profiles the workbook
- user selects sheets or source objects to import
- backend creates a connection record
- backend stores source metadata on the connection

#### Error Handling

- unsupported source type returns validation error
- invalid upload returns validation error
- delete/reset actions should clean up uploaded artifacts when possible

#### Tests

- connection creation
- source metadata persistence
- upload preview generation
- upload cleanup

### 3. Import Orchestration Module

#### Responsibilities

- coordinate the import sequence
- create a run record for each import attempt
- keep import steps in the correct order
- prevent partial success from being treated as complete

#### Control Flow

1. Save the raw upload.
2. Profile the workbook or source object.
3. Create or reuse the connection record as required by the flow.
4. Create the dataset record for each selected source object.
5. Run deterministic cleaning.
6. Persist the cleaned artifact.
7. Create a new dataset version.
8. Update the dataset active version.
9. Record lineage and run outcome.

#### Version Rule

- every re-import creates a new dataset version
- older versions remain available
- version creation only completes after cleaning succeeds

#### Error Handling

- if cleaning fails, keep the raw upload and run record
- if version creation fails, mark the run failed and do not activate the new version
- if the import is partial, surface a warning instead of pretending the dataset is complete

#### Tests

- successful import creates version
- failed cleaning does not activate version
- re-import increments version number

### 4. Cleaning and Dataset Version Module

#### Responsibilities

- clean imported rows deterministically
- persist cleaned outputs as immutable versions
- expose version history and active version state

#### Cleaning Rules

- trim whitespace
- normalize headers
- infer basic types
- remove fully empty rows
- flag invalid cells

#### Data Structures

- `Dataset`
  - `project_id`
  - `connection_id`
  - `name`
  - `source_object_name`
  - `status`
  - `active_version_id`

- `DatasetVersion`
  - `dataset_id`
  - `run_id`
  - `version_number`
  - `status`
  - `row_count`
  - `column_count`
  - `storage_path`
  - `created_at`

- `CleaningResult`
  - `clean_rows`
  - `column_definitions`
  - `row_count`
  - `column_count`
  - `issues`

#### Persistence Decisions

- raw uploaded file is retained separately from the cleaned dataset version
- the cleaned artifact is stored as the version payload
- `storage_path` points to the cleaned artifact
- dataset active version points to the latest successful version

#### Error Handling

- invalid cells become structured issues instead of silent failures
- empty datasets are allowed but should be visibly flagged
- type inference failures should degrade to a safe text representation

#### Tests

- header normalization
- whitespace trimming
- empty-row removal
- type inference
- version incrementing

### 5. Lineage Module

#### Responsibilities

- build the lineage graph for the current dataset
- expose the path from source object to dataset version
- include the run that produced the active version

#### Lineage Model

Recommended node types:

- source object
- connection
- dataset
- dataset version
- run

Recommended edge types:

- imported into
- created
- produced
- activated by

#### Control Flow

- lineage is derived from persisted records
- the workspace requests lineage on page load
- the lineage view renders the current active path and history nodes

#### Error Handling

- if lineage cannot be fully resolved, show the available chain and indicate missing nodes
- missing runs or versions should not block the rest of the workspace

#### Tests

- lineage graph generation
- lineage graph stability across re-imports
- missing-node fallback

### 6. Dataset Workspace Visualization Module

#### Responsibilities

- show read-only cleaned data
- show a small number of chart summaries
- keep the workspace as the main return point for the imported dataset

#### Recommended Workspace Sections

- preview table
- summary cards
- charts panel
- lineage panel
- version history panel

#### Visualization Rules

- charts must use the cleaned dataset version only
- charts must be deterministic
- no editable grid behavior
- no AI-generated chart text

#### Control Flow

- page loads dataset metadata, preview data, versions, health, lineage, and runs
- preview and charts are based on the active version
- switching versions updates the entire workspace basis

#### Error Handling

- if chart data is unavailable, show the table and summary cards without the chart block
- if preview data fails to load, show a clear retry state

#### Tests

- preview rendering
- summary card rendering
- chart rendering from cleaned data
- version switching behavior

### 7. MySQL Readiness Module

#### Responsibilities

- keep MySQL visible in the catalog
- keep the data model ready for a future MySQL import implementation
- avoid special-casing MySQL in the workspace layout

#### Design Rule

- MySQL should use the same connection/dataset/version/lineage shape as static-file imports when it is implemented

#### Tests

- MySQL catalog visibility
- MySQL disabled or not-yet-active state
- shared model compatibility

## Public Interfaces

### Backend

The workbench should expose or extend these API behaviors:

- list source types
- preview and save uploads
- create connections
- create datasets
- fetch dataset metadata
- fetch dataset preview
- fetch dataset versions
- fetch dataset lineage
- fetch dataset health
- fetch run history

### Frontend

The workbench should expose:

- source catalog page
- connection setup page
- dataset workspace page
- preview grid
- summary cards
- lineage view
- version history view

## Persistence Strategy

- source metadata lives on the connection record
- cleaned dataset artifacts live on dataset versions
- the current version lives on the dataset record
- run records track import attempts and outcomes
- lineage is derived from stored records rather than maintained as a separate hidden state machine

## Error Handling Strategy

- use validation errors for unsupported source types and bad input
- use not-found errors for missing datasets or connections
- keep raw artifacts when downstream cleaning fails
- keep failed runs visible for troubleshooting
- do not silently overwrite existing versions

## Test Strategy

### Unit Tests

- cleaning rules
- version increments
- lineage graph builder
- source catalog seeding

### Integration Tests

- static-file import flow
- dataset workspace reads
- re-import creates a new version
- lineage output after import

### Frontend Tests

- source catalog states
- setup flow
- workspace rendering
- read-only visualization and version switching

## Risks

- The current workspace already has tabs for schema, transform, runs, and details, so the v6 visualization surface should stay focused to avoid adding complexity too early.
- Raw file retention needs a clear cleanup policy if imports fail or are discarded.
- MySQL visibility without a working connector can confuse users if the catalog copy is not explicit.
- Cleaning rules must be strict enough to be useful but simple enough to keep deterministic behavior obvious.
