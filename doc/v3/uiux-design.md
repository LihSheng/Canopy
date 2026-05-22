# V3 UI/UX Design: Ingestion Workbench And Lineage Experience

## Purpose

This document captures the agreed v3 UI/UX direction for the data ingestion
and preparation experience.

It is not a visual design-system replacement for [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/Canopy/DESIGN.md). It defines layout,
navigation, hierarchy, page behavior, and interaction rules that v3 should
implement while staying inside the established design language.

## Scope

This document covers the upload, preview, cleaning, lineage, and publish
experience for Excel-based ingestion.

It covers:

- `Upload Wizard`
- `Workbook Preview`
- `Mapping Review`
- `Cleaning Template Builder`
- `Lineage Graph`
- `Publish Review`

It does not define:

- the v1 dashboard shell
- anomaly-rule changes
- export pipeline changes
- LLM-based generation workflows
- mobile-first redesign

## Design direction

V3 should feel like a guided data-prep workspace for non-technical users.

Required design alignment:

- follow [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/Canopy/DESIGN.md)
- keep the interface clear, calm, and task-driven
- use the existing pill, card, spacing, and typography language
- avoid technical jargon where plain labels work better
- make preview and correction the center of the workflow

V3 should optimize for:

- confidence before import
- fast understanding of workbook structure
- safe correction before processing
- visible lineage and version state

V3 should not optimize for:

- visual novelty
- dense admin tables
- hidden automation
- over-complex graph interactions in Phase 1

## Shared ingestion shell

### Navigation model

V3 should use a focused workspace shell rather than a broad product shell.

Primary regions:

- left: upload status and workbook structure
- center: preview and mapping workspace
- right: rules, version state, and lineage summary
- bottom or expandable drawer: lineage graph and validation panel

### Workspace behavior

- upload state should be obvious at all times
- the current sheet should always be visible
- mapping confidence should be visible beside suggestions
- published version state should be visible beside the template name

### Responsive behavior

V3 is desktop-first, but responsive.

Responsive rules:

- desktop is the primary design target
- panels can collapse into drawers on smaller screens
- the preview grid remains the main content
- lineage graph can move below the fold on narrow layouts

## Upload flow

### Role

The upload flow starts the ingestion pipeline.

### Layout intent

The first screen should answer:

- what file was uploaded
- whether the workbook is valid
- which sheet looks like the main data sheet
- what the system thinks the columns mean

### Required states

- empty state
- uploading state
- profiling state
- preview ready state
- mapping review state
- processing state
- completed state
- failed state

### UX rules

- show file name, size, and upload timestamp
- show detected sheet count
- show detected best sheet
- surface warnings early
- keep destructive actions behind confirmation

## Workbook preview

### Role

The preview is the primary trust-building surface.

### Layout intent

The preview should show:

- a sample of real rows
- detected headers
- inferred column types
- confidence labels
- warnings for ambiguous columns

### UX rules

- auto-select the highest-confidence sheet by default
- allow sheet switching without re-upload
- highlight required fields that are still unmapped
- show sample values in a compact but readable format

### Interaction rules

- selecting a column should open mapping detail in-place or in a side panel
- preview rows should remain read-only
- user edits should affect the mapping configuration, not the raw data

## Mapping review

### Role

Mapping review lets the user confirm how workbook columns become canonical
fields.

### Layout intent

The mapping area should show:

- source column name
- suggested target field
- confidence level
- sample values
- required/optional state

### UX rules

- high-confidence suggestions appear prefilled
- low-confidence suggestions require explicit confirmation
- unmapped required fields must be clearly flagged
- one-click bulk actions are allowed only when confidence is high

## Cleaning template builder

### Role

The builder lets users define reusable visual cleaning templates.

### Layout intent

The builder should behave like a rule stack, not a code editor.

It should show:

- ordered steps
- per-step configuration
- input/output preview
- draft vs published state

### UX rules

- editing should feel safe and reversible in draft
- publishing should be a separate action
- each step should be named in plain language
- reusable templates should be easy to clone

### Visual language

Use lightweight cards, step rails, and concise parameter panels.
Avoid dense technical forms unless the rule itself requires them.

## Lineage graph

### Role

The lineage graph is the explanation layer for how data moved through the
pipeline.

### Phase 1 scope

The graph should show:

- file node
- workbook node
- sheet node
- raw column node
- cleaned field node
- ontology-ready field node

### UX rules

- graph is read-only in Phase 1
- graph should be legible without requiring zoom tricks
- graph should support hover details
- graph should have a side panel legend and filtering controls
- graph should not depend on manual layout edits in Phase 1

### Later extension

The same graph surface should be able to show transformation-step nodes later
without redesigning the screen.

## Publish review

### Role

Publish review is the final approval step before a cleaned version becomes
active.

### Layout intent

The review state should show:

- selected template version
- cleaned snapshot summary
- warning count
- field coverage
- lineage summary
- publish confirmation

### UX rules

- do not allow publish if required mappings are missing
- surface warnings before final confirm
- keep publish state explicit
- show the exact version that will become active

## Error states

### Validation errors

Examples:

- unsupported file type
- empty workbook
- no usable sheet found
- missing required field

Behavior:

- use direct, plain-language messages
- keep the upload record available for retry
- preserve the original file

### Processing warnings

Examples:

- mixed data types in a column
- multiple likely header rows
- ambiguous date formats
- low-confidence mapping

Behavior:

- warnings should be visible but not always blocking
- critical warnings should require confirmation

## Interaction principles

- preview before commit
- confirm before publish
- use plain language first
- keep lineage visible, not buried
- let users correct system guesses
- avoid surprise automation

## Visual principles

The design should feel:

- structured
- calm
- deliberate
- data-centric

It should not feel:

- playful
- overdecorated
- code-editor-like
- admin-heavy

## Testable UX expectations

The design should be testable through:

- upload and preview flow
- mapping correction flow
- template publish flow
- lineage graph rendering
- validation and warning display
- responsive collapse behavior

