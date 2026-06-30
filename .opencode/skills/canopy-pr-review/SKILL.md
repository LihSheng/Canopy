# Canopy PR Review Skill

Use this skill whenever you are asked to review or modify Canopy Intelligence code.

## Product Context

Canopy Intelligence is an executive HR spend intelligence platform for C-level users. It consolidates operational HR/source data, maps it into business objects, computes monthly spend views, detects anomalies, and presents dashboard insight plus AI-generated recommendations.

The application is a modular monolith with a FastAPI backend and Next.js frontend. It has strict architectural guardrails because it works with executive HR spend data and snapshot-scoped analytics.

## Source of Truth Reading Order

Before reviewing a meaningful Canopy PR, read these files in order:

1. `ARCHITECTURE.md`
2. `doc/codebase-map.md`
3. `QUICKSTART.md` when test, lint, typecheck, or local execution commands are needed
4. Relevant files changed by the PR

If another document conflicts with `ARCHITECTURE.md`, treat `ARCHITECTURE.md` as the source of truth and call out the conflict.

## Non-Negotiable Architecture Rules

Do not approve a PR that violates any of these rules:

1. The application only performs explicit, audited actions.
   - Reads, writes, approvals, and operational callbacks must go through connector or workflow boundaries.
   - Policy checks and audit logging must be present for operational actions.
   - There must be no hidden side effects into Canopy or upstream systems.

2. Deterministic analytics decide. The LLM narrates.
   - Monthly totals, anomaly detection, rankings, and contributing-driver logic must be computed by application code first.
   - The LLM may receive structured facts and produce explanation text.
   - The LLM must not invent metrics, replace analytics, or become the source of truth for numeric decisions.

3. Dashboard, export, and AI must use the same snapshot basis.
   - UI views, Excel exports, and generated summaries must use the same refresh result.
   - Do not allow dashboard data and AI/export data to drift for the same user-visible snapshot.

## Module Boundary Rules

Check that dependency direction stays clean:

- UI -> API client -> API routes -> services -> repositories / external clients
- sync readers -> mappers -> ontology repositories
- analytics aggregators -> anomaly rules -> insight builders

Flag these problems:

- UI components calling HTTP directly without an adapter boundary
- route handlers containing business rules
- repositories orchestrating business workflows
- anomaly logic depending on HTTP, framework request objects, or UI
- AI prompt builders reaching back into source readers
- large utility/service files mixing unrelated business concerns

## Tenant, Storage, and Audit Rules

When reviewing new code, check that it preserves future multi-tenant seams:

- Avoid assuming one permanent global dataset.
- Avoid assuming one permanent global storage target.
- Use repository or storage-adapter boundaries.
- Pass tenant, snapshot, refresh, or dataset identifiers explicitly where the module needs them.
- Audit meaningful operational actions.
- Keep source-system writes impossible unless they go through an explicit connector or workflow boundary with policy checks.

## Review Checklist

For every Canopy PR review, produce a short review with these sections:

1. Architecture fit
   - Does it follow `ARCHITECTURE.md`?
   - Does it preserve deterministic analytics, snapshot consistency, source read-only safety, and audited boundaries?

2. Correctness and product behavior
   - Does the implementation match the issue or PR description?
   - Are edge cases handled?
   - Are error states and empty states reasonable?

3. Security and data safety
   - Any source-system mutation risk?
   - Any tenant isolation risk?
   - Any audit or authorization gap?
   - Any sensitive data exposed to the LLM or frontend unnecessarily?

4. Tests and validation
   - Are frontend tests, backend tests, lint, typecheck, and business-rule tests updated or clearly not needed?
   - Use the commands in `QUICKSTART.md` when recommending validation.

5. Human decision
   - Choose one: approve, request changes, or needs human decision.
   - Explain the main risk and the files worth human attention.

## Default Validation Commands

Frontend:

```bash
cd apps/frontend && npm run lint && npm run typecheck
cd apps/frontend && npm test
```

Backend:

```bash
cd apps/backend && .venv\Scripts\activate && ruff check . && ruff format --check && mypy .
cd apps/backend && .venv\Scripts\activate && pytest
```

Architecture/business-rule focused backend gates:

```bash
cd apps/backend && .venv\Scripts\activate && pytest -m api_schema -x --tb=long
cd apps/backend && .venv\Scripts\activate && pytest -m business_rule -x --tb=long
```

## How To Review

- Prefer small, specific comments over broad rewrites.
- Do not request changes just because a different implementation style is possible.
- Request changes when the PR violates a non-negotiable rule, creates hidden side effects, weakens snapshot consistency, moves analytics decisions into the LLM, or risks source/tenant data safety.
- Mark `needs human decision` when the change is product-directional, affects executive reporting semantics, changes HR spend definitions, or changes what C-level users will see as a business truth.
