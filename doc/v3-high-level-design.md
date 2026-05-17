# V3 High-Level Design: Data Ingestion, Cleaning, Normalization, and Lineage

> Historical note:
> V3 is the data-preparation phase that follows the completed v2 analytics
> shell work.
> This document defines the architecture for Excel ingestion, workbook
> profiling, visual cleaning templates, immutable snapshots, lineage, and
> ontology-ready publishing.

## Overview

V3 adds a controlled data-preparation layer in front of semantic publishing.
The system remains read-only with respect to source systems, but it now
supports user-driven ingestion of Excel workbooks, deterministic cleaning and
normalization, and explicit lineage tracking from raw input to publishable
output.

The architectural emphasis is:

- preserve the original file
- make raw snapshots immutable
- keep cleaning deterministic and versioned
- expose lineage as first-class data
- let non-technical users review before publish

This is a new product layer, not a rewrite of the v1 analytics baseline.

## Product goals

V3 must enable a guided workflow that feels approachable to non-technical
users while still being rigorous enough for controlled data processing.

Core goals:

- upload any Excel workbook
- inspect workbook structure before processing
- suggest sheet and column mappings
- let users define reusable visual cleaning templates
- produce cleaned and normalized output
- maintain dataset-level and column-level lineage
- publish only approved cleaned versions

## System context

### External inputs

- Excel workbook uploads from users
- later: MySQL and other connector sources

### External dependencies

- current web application and backend stack
- file storage for raw uploads
- workbook parsing library
- database for snapshot, template, lineage, and publish metadata

### Architectural boundary

V3 does not write back to the source workbook or any upstream system.
It stores and transforms only inside application-owned storage.

## Architectural style

V3 should stay within the existing modular-monolith style used by the
application.

Why:

- the data-prep workflow is cohesive
- deterministic processing is easier to test in one backend
- shared storage and lineage state are simpler to coordinate
- the source adapter, cleaner, and publish flow can evolve independently

The main split is:

- synchronous user-facing APIs for upload, preview, mapping review, and
  publish actions
- asynchronous or orchestrated backend flow for parsing, profiling, cleaning,
  normalization, lineage recording, and publish state changes

## Major modules

### 1. Ingestion Workbench

#### Responsibility

Provide the main user workspace for upload, preview, mapping, cleaning, and
publish review.

#### Responsibilities in practice

- present uploaded file state
- show workbook structure and candidate sheet selection
- render preview rows and mapping suggestions
- expose template selection and version state
- display lineage summary and graph entry points
- support publish review and confirmation

#### Interface

- consumes profiling results, preview read models, template state, and lineage
  graph data
- sends mapping decisions, template edits, and publish commands to the API

### 2. Application API

#### Responsibility

Expose typed HTTP endpoints for the ingestion workflow.

#### Main API areas

- upload and file registration
- workbook profiling and preview
- mapping review updates
- template creation and version publishing
- cleaning execution and status
- lineage graph retrieval
- publish review and activation

#### Design intent

This layer stays thin.
It validates requests, delegates to services, and returns typed read models.
It does not own workbook profiling rules or transformation logic.

### 3. Upload and Storage Module

#### Responsibility

Persist the uploaded workbook and the metadata needed to replay or inspect it
later.

#### Responsibilities in practice

- save the original file immutably
- create the upload record
- capture file checksum and source metadata
- expose the storage reference for downstream profiling and preview

#### Important rule

The original uploaded file is never mutated after storage.

### 4. Workbook Profiling Module

#### Responsibility

Inspect uploaded workbooks and generate safe suggestions before processing.

#### Responsibilities in practice

- enumerate sheets
- score candidate sheets
- detect header rows
- infer column types
- estimate mapping confidence
- emit warnings for ambiguous structures

#### Output

This module produces a workbook profile read model, not a persistent
transformation result.

### 5. Preview and Mapping Module

#### Responsibility

Show sampled workbook rows and let the user confirm how source columns map to
canonical fields.

#### Responsibilities in practice

- render preview tables
- surface system suggestions
- capture user overrides
- validate required mappings
- preserve the distinction between raw preview and mapping state

#### Design intent

Preview is a trust-building step, not a transformation step.

### 6. Template and Versioning Module

#### Responsibility

Manage reusable cleaning templates scoped by dataset type and source profile.

#### Responsibilities in practice

- create templates
- manage draft and published states
- create immutable published versions
- bind uploads to specific versions
- support cloning and reuse across uploads

#### Versioning rule

Edits happen in draft.
Publishing creates a new immutable version.

### 7. Cleaning Engine

#### Responsibility

Apply published transformation templates to immutable raw snapshots.

#### Responsibilities in practice

- execute rule stacks deterministically
- trim, rename, cast, parse, dedupe, and normalize values
- produce cleaned snapshots
- record warnings and row issues
- preserve transformation order and configuration

#### Design intent

The cleaning engine is deterministic and explainable. It does not ask the LLM
to decide what transformation should occur.

### 8. Normalization Module

#### Responsibility

Convert cleaned rows into canonical business-ready structures that can later
hydrate ontology mappings.

#### Responsibilities in practice

- standardize field naming
- assign stable identifiers
- prepare normalized dataset records
- preserve the raw-to-cleaned-to-normalized chain

#### Important boundary

Cleaning makes data consistent.
Normalization makes data semantically usable.

### 9. Lineage Module

#### Responsibility

Store and serve lineage as first-class graph data.

#### Responsibilities in practice

- capture file-to-workbook lineage
- capture workbook-to-sheet lineage
- capture source-column-to-cleaned-field lineage
- capture cleaned-field-to-ontology-ready-field lineage
- expose node and edge data to the UI

#### Phase 1 rule

The storage model should be ready for transformation-step lineage even if the
first UI only renders column-level lineage.

### 10. Publish Module

#### Responsibility

Promote one cleaned version into the active ontology-ready state.

#### Responsibilities in practice

- validate required fields and mappings
- validate selected template version
- mark one cleaned version as active
- preserve prior versions
- hand off publish-ready output to downstream ontology hydration

#### Design intent

Publish is a controlled promotion step, not a side effect of cleaning.

### 11. Source Adapter Module

#### Responsibility

Translate source-specific inputs into a generic ingestion contract.

#### Scope

- Excel adapter in Phase 1
- MySQL adapter later

#### Rule

Source-specific parsing and quirks stay in the adapter layer.
The rest of the system consumes generic workbook or source snapshots.

## Data flow

### Happy path

1. User uploads an Excel workbook.
2. Backend stores the file immutably.
3. Workbook profiler analyzes sheets, headers, and columns.
4. UI shows preview rows and mapping suggestions.
5. User confirms or edits the mapping.
6. User selects or edits a cleaning template.
7. Backend executes the published template version.
8. Backend stores a cleaned snapshot and lineage records.
9. Backend normalizes the cleaned output.
10. User reviews and publishes the approved version.

### Data movement rule

Every stage should consume an immutable input and produce a typed output.
No stage should depend on hidden shared mutable state.

## External interfaces

### Frontend to backend

The frontend should call backend APIs for:

- upload
- profile and preview
- mapping updates
- template editing and publishing
- cleaning execution
- lineage retrieval
- publish activation

### Backend to storage

The backend should use storage adapters for:

- raw file storage
- snapshot persistence
- template persistence
- lineage persistence
- publish state persistence

### Backend to workbook parser

The parser adapter should:

- read workbook structure
- sample rows
- extract cell values
- preserve workbook-specific quirks inside the adapter

## Cross-cutting concerns

### Snapshot isolation

All processing is snapshot-scoped.
The upload, raw row snapshot, template version, cleaned snapshot, lineage, and
publish result must refer to explicit versioned identifiers.

### Determinism

Cleaning and normalization must be deterministic for the same input and
template version.

### Source isolation

No raw workbook or MySQL schema knowledge should leak into the API layer,
presentation layer, or downstream analytics logic.

### Auditability

The system must preserve enough metadata to reconstruct:

- which file was uploaded
- which sheet was processed
- which template version was used
- which mappings were chosen
- which cleaned output was published

### User safety

The design should protect non-technical users from accidental overwrite or
hidden mutation.

### Performance

The first version may rely on sample-based preview and deterministic
processing, not aggressive distributed compute.

## Main tradeoffs

### Why a first-class storage model instead of config-only state

Saving templates, steps, snapshots, and lineage as first-class records gives us
queryable provenance and versioned replay.

This is heavier than config-only JSON, but it avoids a dead end when lineage
grows into step-level tracking.

### Why Excel first

Excel is the most accessible source for non-technical users and gives the team
an end-to-end ingestion and lineage experience without connector complexity.

### Why visual rules with deterministic execution

Users need a friendly builder, but the platform still needs predictable
results. The UI expresses intent; the backend executes the saved rule set.

### Why column-level lineage first

Column-level lineage is the right balance between usefulness and complexity.
The data model should already be able to hold step-level lineage later.

## Deferred items

These belong in detailed design, implementation tasks, or later phases:

- exact database tables and indexes
- exact API request and response schemas
- workbook profiling heuristics thresholds
- specific rule operators for the cleaning engine
- lineage graph layout and filtering behavior
- publish-state transitions and retry behavior
- MySQL connector onboarding
- full transformation-step lineage UI

## Summary

V3 introduces a complete user-controlled preparation layer:

- ingest raw Excel
- profile and preview
- map and clean
- version templates
- record lineage
- publish approved output

The core design choice is to keep the system deterministic, immutable where it
matters, and ready for future source connectors without forcing that complexity
into Phase 1.
