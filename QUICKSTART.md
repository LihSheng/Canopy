# Canopy Intelligence — Quick Start

## Prerequisites

- Node.js >= 22
- Python >= 3.11
- npm >= 10
- PostgreSQL 16+ running locally
- Docker Desktop or another way to run the local PostgreSQL container

## Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd "Canopy"

# 2. Install frontend dependencies
cd apps/frontend && npm install && cd ../..

# 3. Create Python virtual environment and install backend
cd apps/backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
cd ../..

# 4. Copy environment files
cp .env.example .env
cp apps/frontend/.env.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env
```

### Start PostgreSQL

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

The backend test harness will create the `canopy_test_control_plane`,
`canopy_test_tenant_data`, and `source_staging_test` databases
automatically if they do not exist.

## Run

**Recommended — use the dev scripts** (they kill old processes first):

```bash
# Start both backend and frontend
powershell -File scripts\dev-start.ps1

# Stop everything
powershell -File scripts\dev-stop.ps1
```

**Manual (not recommended — can leave old processes running):**

```bash
# Terminal 1 — Backend (port 8005)
cd apps/backend
.venv\Scripts\activate
uvicorn app:app --reload --reload-exclude "tests/*" --port 8005

# Terminal 2 — Frontend (port 3005)
cd apps/frontend
npm run dev
```

Open http://localhost:3005

## Test

### Frontend

```bash
# All frontend tests
cd apps/frontend && npm test

# Unit tests only (components, hooks, mappers, formatters)
cd apps/frontend && npm run test:unit

# Integration tests only (page flows, login, dashboard, navigation)
cd apps/frontend && npm run test:integration
```

### Backend

```bash
# All backend tests
cd apps/backend && .venv\Scripts\activate && pytest

# Unit tests only (pure logic — analytics, anomaly rules, mappers, etc.)
cd apps/backend && .venv\Scripts\activate && pytest -m unit

# Integration tests only (DB, API routes, persistence)
cd apps/backend && .venv\Scripts\activate && pytest -m integration

# API schema regression gate (response contracts, DB schema)
cd apps/backend && .venv\Scripts\activate && pytest -m api_schema -x --tb=long

# Core business-rule regression gate (analytics, anomalies, ontology, sync, insights)
cd apps/backend && .venv\Scripts\activate && pytest -m business_rule -x --tb=long

# End-to-end smoke test
cd apps/backend && .venv\Scripts\activate && pytest tests/integration/test_smoke.py -v --tb=long

# With coverage (analytics, anomaly, sync, ontology, insights, exports, refresh, common, auth)
cd apps/backend && .venv\Scripts\activate && pytest --cov=analytics --cov=anomalies --cov=sync --cov=ontology --cov=insights --cov=exports --cov=refresh --cov=common --cov-report=term

# Coverage with XML report
cd apps/backend && .venv\Scripts\activate && pytest --cov=analytics --cov=anomalies --cov=sync --cov=ontology --cov=insights --cov=exports --cov=refresh --cov=common --cov-report=xml
```

## Lint, Format, and Typecheck

```bash
# Frontend
cd apps/frontend && npm run lint && npm run typecheck

# Backend
cd apps/backend && .venv\Scripts\activate && ruff check . && ruff format --check && mypy .
```
