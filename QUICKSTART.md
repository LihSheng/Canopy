# HERD Aggregator — Quick Start

## Prerequisites

- Node.js >= 22
- Python >= 3.11
- npm >= 10

## Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd "HERD Aggregator"

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

## Run

```bash
# Terminal 1 — Backend (port 8000)
cd apps/backend
.venv\Scripts\activate
uvicorn app:app --reload --port 8000

# Terminal 2 — Frontend (port 3000)
cd apps/frontend
npm run dev
```

Open http://localhost:3000

## Test

```bash
# Frontend tests
cd apps/frontend && npm test

# Backend tests
cd apps/backend && .venv\Scripts\activate && pytest

# With coverage
cd apps/backend && pytest --cov=. --cov-report=term
```

## Lint and Typecheck

```bash
# Frontend
cd apps/frontend && npm run lint && npm run typecheck

# Backend
cd apps/backend && ruff check . && mypy .
```
