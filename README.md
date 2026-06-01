# Canopy Intelligence

Executive HR spend intelligence platform. Read-only system for C-level users.

Palantir-like mental model:

- **Ingest + Normalize**: pull operational/source data (read-only) into a product-owned store.
- **Ontology First**: map raw records into stable business objects (departments, employees, claims, payroll, cost centers, budget codes).
- **Deterministic Analytics**: compute monthly spend views + anomalies from code, not from the LLM.
- **Snapshot Everywhere**: dashboard, export, and AI summaries are all bound to the same refresh snapshot.
- **Narrated Insights**: the LLM explains computed facts; it does not invent metrics.

## Non-negotiable rules (from `ARCHITECTURE.md`)

1. Never write back to the source system.
2. Deterministic analytics decide. The LLM narrates.
3. Dashboard, export, and AI use the same snapshot basis.

## What you get (v1–v6 baseline delivered)

- FastAPI backend: auth, source sync, ontology mapping, analytics aggregation, anomaly detection, refresh orchestration, exports, insight generation.
- Next.js frontend: login + executive dashboard shells (summary, trends, departments, anomalies, drill-down).
- Platform modules (delivered across v2–v6): ingestion + cleaning, workspace/dataset, multi-tenant seams + routing, connection workbench.

If you want “where is X implemented?”, start at `doc/codebase-map.md`.

## Repo layout

- `apps/backend` — FastAPI app + domain modules
- `apps/frontend` — Next.js UI
- `doc` — planning/design docs + architecture snapshots
- `infra` / `packages` — light usage / placeholders

## Architecture (high level)

The system is a modular monolith:

- **Sync/Readers** pull from the source DB into staging/snapshot tables.
- **Mappers/Ontology** translate raw source shapes into stable domain objects.
- **Analytics/Anomalies** compute aggregates + rule-based anomaly findings.
- **Refresh Orchestration** coordinates snapshot refresh and job sequencing.
- **Exports/Insights** generate Excel workbooks + narrative summaries tied to the same snapshot.
- **API/UI** serve dashboards + drill-down over snapshot-scoped read models.

Details and guardrails live in `ARCHITECTURE.md` and `doc/`.

## Local dev (Windows quick path)

Prereqs:

- Node.js >= 22, npm >= 10
- Python >= 3.11
- PostgreSQL 16+ (local or Docker)

Setup:

```bash
cd "Canopy"
cp .env.example .env
cp apps/frontend/.env.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env
```

Start PostgreSQL (Docker):

```bash
docker run -d --name canopy-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:16

docker exec canopy-postgres psql -U postgres -d postgres -c "CREATE DATABASE canopy_control_plane;"
docker exec canopy-postgres psql -U postgres -d postgres -c "CREATE DATABASE canopy_tenant_data;"
docker exec canopy-postgres psql -U postgres -d postgres -c "CREATE DATABASE source_staging;"
```

Run backend + frontend:

```bash
# Backend (port 8005)
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app:app --reload --port 8005

# Frontend (port 3005)
cd ../frontend
npm install
npm run dev
```

Open http://localhost:3005

Full setup/test/lint commands: `QUICKSTART.md`.

## Tests

```bash
# Frontend
cd apps/frontend && npm test

# Backend
cd apps/backend && .venv\Scripts\activate && pytest
```

## Docs to read (order)

1. `ARCHITECTURE.md` — system rules + boundaries (source of truth)
2. `QUICKSTART.md` — setup/run/test/lint
3. `doc/codebase-map.md` — “where is what” map
4. `DESIGN.md` — UI visual system
