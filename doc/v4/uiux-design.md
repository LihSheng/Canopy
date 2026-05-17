# V4 UI/UX Design: Data Connection Workspace

## Purpose

This document captures the v4 UI/UX direction for a Data Connection Workspace
inspired by enterprise data platforms.

V4 should make ingestion feel like working with durable data assets, not a
single upload wizard.

## Scope

This document covers:

- Data Connection home
- source catalog
- project/folder context
- dataset list
- dataset detail workspace
- read-only preview grid
- Dataset Health panel
- run progress and run history
- lineage entry points

It does not cover:

- MySQL connection implementation
- advanced access control
- full monitoring/alerting
- direct cell editing

## Design direction

V4 should feel like a quiet operational data workspace:

- dense but organized
- clear navigation
- asset-first
- preview-heavy
- status-aware
- suitable for repeated use by non-technical and semi-technical users

The interface should not feel like a marketing page or a decorative dashboard.
It should feel like a working surface.

## Data Connection home

The home page should be a launchpad.

Primary areas:

- `New source` action
- source setup cards
- recent datasets
- recent runs
- project context

Source setup cards:

- `Connect external system`
- `Upload static data`
- `Input or generate data`

Only `Upload static data` is enabled in the first v4 implementation.

## Source catalog

The catalog should show enabled and future source types.

Enabled:

- Excel / Static file

Disabled future cards:

- MySQL
- PostgreSQL
- REST API
- Google Sheets
- CSV

Disabled cards should open an information panel instead of acting as dead
links.

## Project and file context

V4 should include a simple project layer.

Project workspace areas:

- files/datasets
- connections
- runs
- details side panel

Advanced permissions and sharing are out of scope.

## Dataset workspace

The dataset page should be the main working surface.

Recommended tabs:

- `Preview`
- `Schema`
- `Transform`
- `Lineage`
- `Runs`
- `Details`

Preview is read-only.
All modifications happen through mapping and transform rules.

## Dataset Health panel

Show a compact health panel in the dataset workspace.

Initial fields:

- row count
- column count
- missing required mappings
- warning count
- last run status
- last published version
- data freshness timestamp

Health should be visible from the dataset page and summarized in dataset lists.

## Run progress and history

V4 should show current run progress inside the dataset page.

Run history should show:

- status
- duration
- started by
- start time
- output version
- warning count

A full cross-dataset build tracker is deferred.

## Lineage entry

Lineage should be reachable from:

- dataset detail page
- run detail
- dataset list action

The graph remains read-only unless a later phase explicitly changes that.

## Library usage

Recommended libraries:

- `glide-data-grid` for preview grid
- `@xyflow/react` for lineage graph
- `lucide-react` for icons

The workspace shell, source catalog, side panels, tabs, and run panels should
remain custom React/Tailwind components so the product can match the existing
system.

