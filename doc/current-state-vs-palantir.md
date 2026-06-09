# Canopy Current State vs Palantir-Style Platform

This note documents the current Canopy codebase and compares it with the
Palantir Foundry / Ontology / Workshop style of platform.

Use this as a current-state guide, not a product promise.

## What Canopy Is Today

Canopy is a read-only HR and spend intelligence platform. The repo is organized
as a modular monolith with:

- `Next.js + TypeScript` frontend
- `FastAPI + Python` backend
- `Postgres`-backed application storage
- background refresh, sync, analytics, anomaly, export, and summary flows

The architectural source of truth is [ARCHITECTURE.md](../ARCHITECTURE.md).
The current module snapshot is in [doc/codebase-map.md](./codebase-map.md).

Core rules in the current system:

- no write-back to the source system
- deterministic analytics first, LLM narration second
- dashboard, export, and AI summary must share the same snapshot basis

## What Has Been Built

The current codebase already has these major surfaces:

- authentication and session handling
- source sync and normalization into internal business objects
- ontology-style domain mapping with source lineage preserved on records
- analytics aggregation and department/spend breakdowns
- anomaly detection and anomaly detail views
- export generation from the same derived data basis as the dashboard
- refresh orchestration and job tracking
- tenant/control-plane and data-plane modules
- dataset and connection workbench flows
- entity-focused frontend flows and entity lineage visualizations

Concrete code areas worth reading:

- [apps/backend/api/routes/semantic.py](../apps/backend/api/routes/semantic.py)
- [apps/backend/api/routes/entities.py](../apps/backend/api/routes/entities.py)
- [apps/backend/ontology](../apps/backend/ontology)
- [apps/backend/ingestion](../apps/backend/ingestion)
- [apps/frontend/src/components/entity-helper/entity-add-flow.tsx](../apps/frontend/src/components/entity-helper/entity-add-flow.tsx)
- [apps/frontend/src/components/entity-graph/entity-lineage-canvas.tsx](../apps/frontend/src/components/entity-graph/entity-lineage-canvas.tsx)

## Comparison To Palantir

Palantir’s public docs describe Foundry as an enterprise data operating system
with a data layer, an Ontology layer, Object Views, Workshop applications,
actions, lineage, and branching workflows. See:

- [Foundry platform summary](https://www.palantir.com/docs/foundry/getting-started/foundry-platform-summary-llm)
- [Ontology system](https://www.palantir.com/docs/foundry/architecture-center/ontology-system)
- [Ontology Manager](https://www.palantir.com/docs/foundry/ontology-manager/overview/index.html)
- [Object Views overview](https://www.palantir.com/docs/foundry/object-views/overview/)
- [Workshop overview](https://www.palantir.com/docs/foundry/workshop/overview)
- [Data Lineage navigation](https://www.palantir.com/docs/foundry/data-lineage/navigation/)
- [Action log](https://www.palantir.com/docs/foundry/action-types/action-log)

### Where Canopy already resembles Palantir

- Canopy has a semantic/ontology-shaped backend with domain objects, source
  lineage, and mapping logic.
- Canopy has entity-centric UI surfaces, including a central entity manager
  direction and lineage graphs.
- Canopy has dataset/workbench flows that behave like a guided data prep layer.
- Canopy has a governed refresh/export/snapshot model instead of ad hoc reads.
- Canopy already separates raw source reading from normalized downstream models.

### Where Canopy is still behind Palantir

- No true ontology action system yet.
  - Canopy has helper flows and preview-oriented entry points.
  - Palantir has explicit action types, action rules, and action logs.
- No first-class Object View / Workshop framework.
  - Canopy has custom React screens and entity pages.
  - Palantir has reusable object views and a declarative app-building layer.
- No fully mature object-layer governance depth.
  - Canopy has tenant/control-plane modules and audit/telemetry direction.
  - Palantir treats governance, actions, and ontology workflows as tightly
    integrated platform primitives.
- No branching ontology workflow comparable to Foundry’s branching support.
  - Canopy has versioning and lineage, but not the same branch/merge model.
- No source write-back or operational action execution.
  - Canopy stays read-only by design.
  - Palantir supports action-driven edits inside the ontology.

## Bottom Line

Canopy is not a Palantir clone. It is a narrower, read-only intelligence
platform that already borrows the same structural ideas:

- source isolation
- normalized business objects
- lineage
- guided entity management
- governed snapshots
- analytics plus AI narration

What is missing is the deeper Palantir-style platform layer:

- action semantics
- reusable object-view tooling
- branchable ontology management
- stronger governance and operational rigor around the object layer

That gap is exactly where the newer entity-manager, lineage-canvas, and
platform-hardening PRDs are pointing.
