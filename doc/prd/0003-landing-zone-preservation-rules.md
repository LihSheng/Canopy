# PRD: Landing-Zone Preservation Rules for Source Ingestion

**Status:** Ready for implementation
**Date:** 2026-05-28
**Scope:** Backend ingestion, dataset/versioning, run orchestration, API validation

---

## Problem Statement

Current ingestion behavior does not enforce a strict immutable raw landing boundary across all source types. In particular, ingestion paths can apply or couple cleaning behavior too early (especially for static file flow), and ingestion APIs do not explicitly reject transformation-oriented settings. This creates risk that source-of-truth raw data is altered before downstream transformation stages, making replay/reproducibility weaker and blurring fault boundaries.

The product needs a hard ELT boundary:
- Ingestion/Landing must preserve source structure exactly as received.
- Transformation settings must be rejected during ingestion configuration.
- Downstream transformation failures must never mutate or roll back preserved landing data.

## Solution

Implement a landing-zone preservation guardrail set that enforces immutability at ingestion for all supported source types (`static_file`, `mysql`, `postgresql`):

1. Preserve source structure at landing:
- Ingestion writes raw landed artifacts as-is into raw landing storage.
- No rename, drop, cast, filtering, or masking at landing stage.

2. Reject transformation settings at ingestion APIs:
- Any ingestion payload containing transformation-oriented keys is rejected with 422 and explicit blocked keys.

3. Isolate downstream failure impact:
- Landing commit and downstream transform state are decoupled.
- If transform fails, raw landing artifact stays preserved and immutable.
- Active transformed dataset pointer remains on last successful transformed version (no failed promotion).

## User Stories

1. As a data engineer, I want raw landed data to be stored exactly as received, so that I can always reconstruct historical data.
2. As a data engineer, I want ingestion to reject transformation settings, so that ETL boundaries stay clear and enforceable.
3. As a platform maintainer, I want landing and transform phases separated, so downstream failures cannot corrupt raw historical records.
4. As an analyst, I want failed downstream runs to leave the current published transformed view unchanged, so dashboards do not point at broken results.
5. As an auditor, I want immutable raw artifacts retained after downstream failures, so I can validate provenance and replay pipelines.
6. As a developer, I want deterministic validation errors listing blocked ingestion keys, so I can quickly correct payloads.
7. As a developer, I want one invariant for all source types, so behavior is predictable across static file and database connectors.
8. As an operator, I want run failure states to be explicit without deleting landed data, so incident recovery is fast and safe.
9. As a product owner, I want transformation logic constrained to downstream jobs, so feature evolution does not risk source corruption.
10. As a tenant admin, I want immutability guarantees preserved under tenant isolation constraints, so trust and compliance are maintained.
11. As a QA engineer, I want regression tests proving no landing mutation on transform failure, so boundary regressions are caught early.
12. As a backend engineer, I want clear contracts for ingestion vs transformation modules, so code ownership and testing seams stay clean.
13. As a data reliability engineer, I want idempotent landing behavior independent of transform results, so retries are safe.
14. As a support engineer, I want precise 422 error messaging for rejected settings, so customer troubleshooting is straightforward.
15. As a governance stakeholder, I want raw-zone immutability encoded as code-level rules, so policy is enforceable by default.

## Implementation Decisions

- Apply preservation rules to all ingestion source types currently in use: static file, MySQL, PostgreSQL.
- Introduce a shared ingestion validation guard that blocks transformation-oriented keys in ingestion-stage payloads.
- Enforce blocked-key denylist at ingestion API boundaries with consistent 422 response contract:
  - `code`: `INGESTION_TRANSFORM_NOT_ALLOWED`
  - `message`: `Transformation settings are not allowed at landing stage`
  - `blocked_keys`: list of violating keys
- Initial blocked ingestion keys:
  - `transformations`
  - `cleaning_steps`
  - `column_mappings`
  - `rename_columns`
  - `drop_columns`
  - `cast_rules`
  - `filters`
  - `masking_rules`
  - `normalization_rules`
- Refactor static-file ingestion path to remove ingest-time cleaning from landing write flow.
- Keep raw landing artifact reference captured on dataset version metadata and preserve immutability semantics.
- Preserve separate lifecycle states for landing success and transform success; transform failure must not invalidate landing commit.
- Prevent failed downstream transforms from promoting active transformed version pointers.
- Keep architecture aligned with source isolation and snapshot consistency rules.
- No changes to user-facing analytics semantics except stricter ingestion validation and safer failure behavior.

## Testing Decisions

- Good tests assert external behavior and contracts, not internal implementation wiring.
- Validate boundary contracts through API behavior, dataset-version state transitions, and raw artifact invariants.
- Required test coverage:
  - ingestion validation rejects blocked transformation keys with deterministic 422 payload
  - static-file ingestion lands raw structure without mutation at landing stage
  - mysql/postgresql ingestion preserves landed source row/column structure
  - downstream transform failure keeps raw artifact unchanged
  - downstream transform failure does not promote failed transformed version
  - existing preview/reimport/refresh flows remain stable under new boundary
- Prior art to extend:
  - existing dataset service/unit tests
  - dataset refresh and reimport integration tests
  - connection and ingestion API validation tests

## Out of Scope

- New transformation features or cleaning-rule UX redesign.
- New connector types beyond current source set.
- CDC implementation changes beyond current ingestion behavior.
- Full lineage model redesign.
- Cross-tenant policy redesign.
- Dashboard/export logic changes unrelated to landing immutability.
- Historical backfill migration of previously landed transformed artifacts.

## Further Notes

- This PRD enforces an explicit ELT contract already implied by architecture guardrails: source isolation, snapshot consistency, and deterministic downstream processing.
- Existing source records remain usable as downstream inputs; immutability means no landing-stage mutation, not no read access.
- If issue-tracker automation is unavailable in local runtime, this PRD document is the publish-ready source text for manual issue creation with the `needs-triage` label.
