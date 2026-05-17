# Quality Guardrails & Review Checklist

## Purpose

This document defines review checklist items and guardrails for preventing
untestable mixed-responsibility modules. These supplement the architecture
rules in `ARCHITECTURE.md`.

---

## Review Checklist

Before merging any change, verify:

### Modularity

- [ ] Does the change follow dependency direction (UI → API → services → repositories)?
- [ ] Are route handlers free of business logic (no analytics formulas, no anomaly rules)?
- [ ] Do repositories call only database/client code, not other repositories?
- [ ] Are source-schema details isolated inside sync readers / source-facing mappers?

### Testability

- [ ] Can the core logic be tested without booting the full app or framework?
- [ ] Are there pure function tests for any new analytics, anomaly, or formatting rules?
- [ ] Are there integration tests for any new API route or persistence path?
- [ ] If the module accepts a storage or client dependency, is it injectable (interface/ABC or callable)?

### Regression Protection

- [ ] If the change touches analytics, ontology, or anomaly logic, does it have a `business_rule`-marked test?
- [ ] If the change touches API response schemas, do the `api_schema`-marked tests pass?
- [ ] If the change adds or renames database columns/tables, is `test_schema_verification.py` updated?

### CI Stages

- [ ] Do `npm run test:unit` and `npm run test:integration` pass in `apps/frontend`?
- [ ] Do `pytest -m unit` and `pytest -m integration` pass in `apps/backend`?
- [ ] Does `pytest -m api_schema -x` pass (no schema regressions)?
- [ ] Does `pytest -m business_rule -x` pass (no business-logic regressions)?
- [ ] Does the smoke test pass: `pytest tests/integration/test_smoke.py -v`?

---

## Guardrails for Untestable Mixed-Responsibility Modules

### Rule 1: One responsibility per module

If a module does more than one thing, split it.

Signs of mixed responsibility:
- A file named `service.py` that both queries data AND formats output
- A route handler that computes analytics values inline
- A repository that also contains business rules
- A mapper that also writes to storage

### Rule 2: Framework code must not contain domain logic

FastAPI request/response objects, SQLAlchemy session management, and other
framework concerns belong at the edges. If a business-rule test needs to
import a framework object, the boundary has been crossed.

### Rule 3: Storage adapters must be swappable

Business services should accept storage through an interface (ABC or
callable), not hardcode a global session. This rule may be relaxed for
V1 as long as the wiring is centralized and visible in one place.

### Rule 4: Hardcoded data patterns must be replaced before production

Any test that relies on hardcoded sample data (not fixture-generated)
must be flagged for removal before the module is considered "not stub."

### Rule 5: Every CI gate must have at least one failing test scenario

For each gated test marker (`api_schema`, `business_rule`), there must be
a test case that verifies the gate catches a regression. This ensures the
gate is not vacuously passing.

---

## Verifying CI Gates

```bash
# Run all gates locally before pushing
cd apps/backend

# Schema contracts
pytest -m api_schema -x --tb=long

# Business rules  
pytest -m business_rule -x --tb=long

# Smoke path
pytest tests/integration/test_smoke.py -v --tb=long

# Coverage summary
pytest --cov=analytics --cov=anomalies --cov=sync --cov=ontology --cov=insights --cov=exports --cov=refresh --cov=common --cov-report=term

cd apps/frontend
npm run test:unit && npm run test:integration
```
