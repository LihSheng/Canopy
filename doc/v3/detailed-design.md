# V3 Detailed Design: Data Ingestion, Cleaning, Normalization, and Lineage

## Purpose

This document expands the v3 high-level design into implementation-ready
module detail for Excel ingestion, workbook profiling, guided mapping,
deterministic cleaning, normalization, lineage, and publish control.

It is the v3 counterpart to the completed v2 analytics shell work. It does not
replace [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

## Source documents

This design follows:

- [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
- [`doc/v3/plan.md`](../../doc/v3/plan.md)
- [`doc/v3/high-level-design.md`](../../doc/v3/high-level-design.md)
- [`doc/v3/uiux-design.md`](../../doc/v3/uiux-design.md)

If these documents conflict, `ARCHITECTURE.md` remains the source of truth for
system boundaries and `doc/v3/plan.md` remains the source of truth for v3
scope.

## V3 scope

V3 is the controlled raw-data platform phase.

V3 delivers:

- Excel upload and file storage
- workbook profiling and preview
- guided mapping review
- reusable cleaning templates with versioning
- deterministic cleaning and normalization
- immutable raw and cleaned snapshots
- column-level lineage
- ontology-ready publish activation

V3 does not deliver:

- source-system write-back
- LLM-driven transformation decisions
- general multi-source ingestion on day one
- editable raw snapshots after upload
- full step-level lineage UI in Phase 1

## Module map

### Frontend modules

- `v3-ingestion-workbench`
- `v3-upload-wizard`
- `v3-workbook-profiler`
- `v3-mapping-review`
- `v3-cleaning-template-builder`
- `v3-template-library`
- `v3-lineage-graph`
- `v3-publish-review`

### Backend modules

- `v3.ingestion.api`
- `v3.ingestion.orchestration`
- `v3.ingestion.storage`
- `v3.ingestion.sources.xlsx`
- `v3.ingestion.profiling`
- `v3.ingestion.preview`
- `v3.ingestion.mapping`
- `v3.ingestion.templates`
- `v3.ingestion.cleaning`
- `v3.ingestion.normalization`
- `v3.ingestion.lineage`
- `v3.ingestion.publish`

### Shared domain modules

- `ingestion-domain`
- `workbook-profile`
- `mapping-suggestions`
- `template-spec`
- `cleaning-step-spec`
- `lineage-model`
- `publish-state`

## Module responsibilities

### 1. Ingestion Workbench

#### Responsibility

Host the end-to-end user journey from upload to publish review.

#### Responsibilities in practice

- show upload state
- show workbook structure
- show preview and mapping review
- show template selection
- show lineage graph and warnings
- show publish review and activation controls

#### Internal rules

- workbench state is composed from backend read models
- the workbench does not infer workbook structure itself
- graph rendering is read-only in Phase 1

### 2. Upload Wizard

#### Responsibility

Create the initial upload record and hand the workbook to the profiling flow.

#### Responsibilities in practice

- validate file type and size
- validate that the workbook is readable
- persist the original file immutably
- create an upload snapshot record
- kick off profiling and preview generation

#### Public interface

```ts
type UploadWorkbookRequest = {
  file_name: string
  source_profile: string
  dataset_type: string
}
```

```ts
type UploadWorkbookResult = {
  upload_id: string
  status: 'uploaded' | 'profiled' | 'failed'
  storage_path: string
  checksum: string
}
```

#### Persistence decisions

- original workbook is stored once
- upload metadata is immutable after creation
- failed uploads remain queryable

### 3. Workbook Profiler

#### Responsibility

Inspect the uploaded workbook and generate profile data without mutating
anything.

#### Responsibilities in practice

- enumerate sheets
- identify likely data sheets
- detect likely header rows
- sample rows
- infer column types
- generate mapping confidence values
- emit warnings for ambiguity

#### Key data structures

```ts
type WorkbookProfile = {
  upload_id: string
  best_sheet_name: string | null
  sheet_profiles: SheetProfile[]
  column_profiles: ColumnProfile[]
  warnings: string[]
}
```

```ts
type SheetProfile = {
  sheet_name: string
  row_count: number
  column_count: number
  header_row_index: number | null
  confidence: number
  warnings: string[]
}
```

```ts
type ColumnProfile = {
  source_column_name: string
  inferred_type: 'text' | 'number' | 'date' | 'boolean' | 'mixed'
  sample_values: string[]
  null_ratio: number
  confidence: number
  suggested_target_field: string | null
}
```

#### Output contract

Profiling returns a read model and a suggestion model.
It does not perform cleaning.

### 4. Preview and Mapping Module

#### Responsibility

Show sampled workbook rows and let the user confirm or override source-to-field
mappings.

#### Responsibilities in practice

- render preview rows from the stored workbook
- show inferred headers and column types
- show suggested target fields
- capture user overrides
- validate required mappings

#### Public interface

```ts
type MappingSuggestion = {
  source_column_name: string
  target_field_name: string
  confidence: number
  required: boolean
  sample_values: string[]
}
```

```ts
type MappingDecision = {
  source_column_name: string
  target_field_name: string
  confirmed: boolean
  overridden_by_user: boolean
}
```

#### Rules

- preview rows are always read-only
- mapping decisions are saved separately from raw data
- required fields must be explicitly resolved before publish

### 5. Cleaning Template Module

#### Responsibility

Create and manage reusable template definitions for data cleaning and
standardization.

#### Responsibilities in practice

- create template families
- create draft versions
- publish immutable versions
- clone from existing versions
- bind uploads to specific versions

#### Template scope

Templates are scoped by:

- dataset type
- source profile

#### Key data structures

```ts
type CleaningTemplate = {
  id: string
  dataset_type: string
  source_profile: string
  name: string
  status: 'draft' | 'published'
  current_version: number
}
```

```ts
type CleaningTemplateVersion = {
  id: string
  template_id: string
  version_number: number
  state: 'draft' | 'published'
  spec_json: Record<string, unknown>
}
```

#### Versioning rule

Edits happen only in draft.
Publishing creates a new immutable version.

### 6. Cleaning Engine

#### Responsibility

Apply the selected published template version to the raw workbook snapshot.

#### Responsibilities in practice

- trim whitespace
- normalize null-like values
- rename columns
- parse dates
- cast values
- deduplicate rows
- filter invalid empty rows
- emit warnings and failures

#### Supported Phase 1 rule families

- trim
- rename
- cast
- parse_date
- dedupe
- normalize_nulls
- filter_empty_rows

#### Key data structures

```ts
type CleaningStep = {
  id: string
  step_type: string
  order: number
  parameters: Record<string, unknown>
}
```

```ts
type CleaningRunResult = {
  cleaned_snapshot_id: string
  status: 'completed' | 'completed_with_warnings' | 'failed'
  warning_count: number
  row_count: number
}
```

#### Execution rules

- steps run in a fixed order
- the engine consumes immutable input only
- the engine returns explicit warnings
- the engine never mutates the raw snapshot

### 7. Normalization Module

#### Responsibility

Convert cleaned rows into canonical structures ready for ontology hydration.

#### Responsibilities in practice

- standardize field names
- enforce canonical value formats
- assign stable identifiers
- preserve source references

#### Design intent

Normalization is semantic preparation, not a second cleaning pass.

### 8. Lineage Module

#### Responsibility

Persist lineage records and expose graph data to the UI.

#### Responsibilities in practice

- create lineage nodes
- create lineage edges
- store file, workbook, sheet, column, cleaned field, and ontology-ready
  field relationships
- support graph queries by upload, template version, and snapshot

#### Key data structures

```ts
type LineageNode = {
  id: string
  node_type: 'file' | 'workbook' | 'sheet' | 'raw_column' | 'cleaned_field' | 'ontology_field'
  label: string
  metadata: Record<string, unknown>
}
```

```ts
type LineageEdge = {
  id: string
  from_node_id: string
  to_node_id: string
  edge_type: 'derived_from' | 'mapped_to' | 'normalized_to'
  metadata: Record<string, unknown>
}
```

#### Phase 1 rule

The graph should show column-level lineage first.
The storage model must still be able to add transformation-step lineage later
without schema redesign.

### 9. Publish Module

#### Responsibility

Promote an approved cleaned version into active publish state.

#### Responsibilities in practice

- validate mapping completeness
- validate required field coverage
- validate selected template version
- activate one cleaned version
- preserve prior versions
- hand off publish-ready output

#### Key data structures

```ts
type PublishState = {
  cleaned_snapshot_id: string
  active: boolean
  published_at: string | null
}
```

#### Rules

- publish is separate from cleaning
- only one active publish state exists per binding
- prior published versions remain queryable

### 10. Excel Source Adapter

#### Responsibility

Parse workbook-specific structures into a generic ingestion contract.

#### Responsibilities in practice

- read sheets and rows
- preserve raw cell values
- handle merged cells and alternate header rows
- isolate workbook-specific quirks

#### Why this stays separate

Workbook quirks are source-specific concerns.
Keeping them in the adapter prevents leakage into profiling or cleaning logic.

## Control flow

### Upload to profile

1. User uploads workbook.
2. Backend stores the file.
3. Upload snapshot is created.
4. Excel adapter parses workbook structure.
5. Workbook profiler scores sheets and columns.
6. Preview read model is returned.

### Review to clean

1. User confirms or edits mapping.
2. User chooses or edits a cleaning template draft.
3. User publishes a template version.
4. Backend loads the selected published version.
5. Cleaning engine runs against the immutable raw snapshot.
6. Cleaned snapshot and lineage records are stored.

### Clean to publish

1. User reviews cleaned output and warnings.
2. Backend validates publish prerequisites.
3. Backend activates the cleaned version.
4. Publish state is written.
5. Downstream ontology hydration can consume the approved output.

## Persistence design

### Logical storage zones

- raw file storage
- upload metadata
- workbook profile data
- mapping decisions
- template families
- template versions
- raw row snapshots
- cleaned snapshots
- lineage records
- publish state

### Persistence rules

- raw file is immutable
- raw row snapshot is immutable
- template version is immutable after publish
- cleaned snapshot is immutable
- lineage records are append-only
- publish state is explicit and versioned

## API design

### Suggested route groups

- `POST /api/v3/ingestion/uploads`
- `GET /api/v3/ingestion/uploads/{upload_id}`
- `GET /api/v3/ingestion/uploads/{upload_id}/preview`
- `POST /api/v3/ingestion/uploads/{upload_id}/mapping`
- `GET /api/v3/ingestion/templates`
- `POST /api/v3/ingestion/templates`
- `GET /api/v3/ingestion/templates/{template_id}`
- `POST /api/v3/ingestion/templates/{template_id}/publish`
- `POST /api/v3/ingestion/uploads/{upload_id}/process`
- `GET /api/v3/ingestion/uploads/{upload_id}/lineage`
- `POST /api/v3/ingestion/publish/{cleaned_snapshot_id}`

### Contract rules

- request DTOs are typed
- response payloads are typed read models
- preview responses include warnings and confidence
- lineage endpoints return node and edge arrays
- processing endpoints return explicit run states

## Error handling

### Validation errors

Examples:

- unsupported file type
- unreadable workbook
- empty workbook
- missing required mappings

Behavior:

- fail before processing starts
- preserve the upload record
- surface human-readable messages

### Processing warnings

Examples:

- mixed type columns
- low-confidence mappings
- ambiguous header rows
- partially empty rows

Behavior:

- continue when safe
- attach warnings to the run and lineage
- block publish when required data is missing

### Hard failures

Examples:

- file corruption
- parser failure
- storage failure
- template execution failure

Behavior:

- mark the run failed
- preserve previous immutable state
- store failure reason for recovery

## Test strategy

### Unit tests

Cover:

- sheet scoring
- header detection
- column inference
- mapping suggestion ranking
- template version transitions
- cleaning step execution
- lineage node and edge creation
- publish validation rules

### Integration tests

Cover:

- upload to profile flow
- preview retrieval flow
- mapping persistence flow
- cleaning execution flow
- lineage API flow
- publish activation flow

### UI tests

Cover:

- upload wizard
- workbook preview
- mapping review
- template builder
- lineage graph
- publish confirmation

## Implementation risks

### Workbook variability

Excel files differ wildly in structure.

Mitigation:

- profiling heuristics
- preview-first UX
- explicit user confirmation

### Over-automation

Auto-suggestion can become wrong if treated as truth.

Mitigation:

- confidence display
- manual overrides
- publish gating

### Version drift

Reusable templates can diverge from the behavior used for older uploads.

Mitigation:

- draft/published lifecycle
- immutable versions
- upload binding to exact version

### Graph complexity

Step-level lineage can become noisy if modeled too early.

Mitigation:

- column-level lineage in Phase 1
- first-class lineage storage
- later UI expansion from the same backbone

## Deferred items

These belong in implementation tasks or later phases:

- detailed workbook profiling heuristics
- exact rule parameters for the cleaning engine
- exact persistence schemas and indexes
- exact graph layout and filtering behavior
- MySQL adapter implementation
- full step-level lineage UI

## Summary

The detailed design makes v3 executable:

- upload and store Excel files immutably
- profile and preview without mutation
- collect mapping and template decisions
- execute deterministic cleaning
- normalize cleaned output
- record lineage
- publish one approved version at a time
