# V2 Plan

## Purpose

This document is the active planning entrypoint for v2.

Use it to describe what changes after the completed v1 baseline, why those
changes matter, and what architectural constraints must hold during the next
delivery phase.

## V1 baseline

As of May 16, 2026:

- v1 is complete
- the system is a modular monolith
- the source system remains read-only
- dashboard, export, refresh, and insight flows are snapshot-based
- auth is simple email/password
- the primary user flow is executive spend visibility and drill-down

Baseline references:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/Canopy/ARCHITECTURE.md)
- [`doc/v1/high-level-design.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/v1/high-level-design.md)
- [`doc/v1/detailed-design.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/v1/detailed-design.md)
- [`doc/codebase-map.md`](C:/Users/Lih%20Sheng/Documents/Canopy/doc/codebase-map.md)

## What v2 should not do

V2 should not:

- rewrite the codebase without a strong product reason
- break snapshot consistency between dashboard, export, and insight outputs
- bypass modular service, repository, and adapter boundaries
- mix raw source schema logic into analytics, API, or frontend modules
- add features that silently undo testability or modularity

## Candidate v2 directions

These are the most obvious post-v1 expansion areas from the completed baseline.
They are candidates, not yet committed scope.

### 1. Multi-tenant readiness beyond current seams

Possible work:

- tenant-aware request/job context
- storage routing abstraction
- stronger separation between application storage and analytics storage

### 2. Additional source connectors

Possible work:

- connector abstraction over source sync readers
- connector-specific normalization pipelines
- source onboarding and monitoring flows

### 3. Stronger access control

Possible work:

- role-based access control
- department/entity-scoped access
- later SSO support

### 4. Richer analytics and anomaly logic

Possible work:

- more anomaly rule types
- better threshold tuning and configuration
- more consistent employee-level payroll drill-down where data quality allows

### 5. Insight and reporting improvements

Possible work:

- stronger provenance and explanation structure
- richer export formats
- better refresh/status reporting

## Required v2 planning questions

Before committing v2 scope, answer:

1. Which v1 limitations are product blockers versus “nice to have”?
2. Is v2 about scale, tenants, connectors, access control, analytics depth, or UX depth?
3. Which changes alter storage shape or request context?
4. Which changes require backward-compatible API expansion versus contract breaks?
5. Which features can reuse the current snapshot pipeline and which require a new flow?

## Architecture guardrails

V2 planning must preserve:

- modular monolith boundaries unless there is a proven extraction need
- plain typed business logic that is testable without framework boot
- snapshot-scoped data flow
- source isolation
- deterministic analytics before AI narration

## Suggested next v2 docs

When v2 scope is chosen, create:

- `doc/v2/uiux-design.md`
- `doc/v2/detailed-design.md`
- `doc/v2-requirements.md`
- `doc/v2-high-level-design.md`
- `doc/v2-task-breakdown.md`

Do not overwrite the v1 baseline docs with speculative v2 scope.
