# V3 Plan

## Purpose

This document is the active planning entrypoint for v3.

V3 is the data ingestion and preparation phase:

- Excel upload ingestion
- workbook profiling and preview
- guided column mapping
- visual no-code cleaning templates
- reusable template versioning
- immutable raw and cleaned snapshots
- column-level lineage
- ontology-ready publishing

## Baseline

V2 is the completed analytics-shell and dashboard UX phase.
The v3 work builds a new data-prep layer that sits before ontology hydration
and before any future connector expansion.

## What v3 should not do

V3 should not:

- write back into source systems
- turn cleaning into LLM-driven guessing
- expose raw file mutation after upload
- overwrite old cleaned results
- hide lineage inside opaque config blobs
- break the existing read-only analytics baseline

## Candidate v3 directions

These are the committed v3 areas.

### 1. Excel ingestion and preview

Possible work:

- upload wizard
- workbook profiling
- sheet detection
- preview grid
- mapping suggestions

### 2. Cleaning templates and versioning

Possible work:

- reusable templates
- draft and published states
- version binding per upload
- visual rule builder

### 3. Raw and cleaned storage

Possible work:

- immutable file storage
- immutable raw row snapshots
- immutable cleaned outputs
- execution metadata

### 4. Column-level lineage

Possible work:

- source file to sheet lineage
- source column to cleaned field lineage
- cleaned field to ontology-ready property lineage

### 5. Publish flow

Possible work:

- publish review panel
- validation gates
- active version activation
- ontology-ready output handoff

## Required v3 planning questions

Before implementing v3, answer:

1. Which upload and preview states must be blocking versus warning-only?
2. Which cleaning rules are mandatory in Phase 1?
3. Which lineage nodes must be stored as first-class DB objects?
4. Which API endpoints are needed for the first usable workflow?
5. Which parts of the graph can be rendered read-only in Phase 1?

## Architecture guardrails

V3 planning must preserve:

- modular monolith boundaries
- plain typed business logic
- immutable raw and cleaned snapshots
- source isolation
- deterministic execution before any semantic publishing

## Suggested next v3 docs

When v3 scope is chosen, create:

- `doc/v3/uiux-design.md`
- `doc/v3/high-level-design.md`
- `doc/v3/detailed-design.md`
- `doc/tasks/v3/progress.md`
