# TODO: Schema Drift Follow-ups (Post-v1)

This file records planned enhancements for the Schema Drift circuit breaker after `doc/prd/0004-schema-drift-circuit-breaker.md` v1 ships.

## Lineage + transformation blocking

- Add explicit “transformation job/model” entities (or reuse existing ones if present) so we can block downstream transformations, not only dataset materialization.
- Integrate with lineage graph to compute affected downstream nodes and block only those nodes.
- Add “blocked reason” fields per node and per dataset.
- Add UI surface for downstream blocked nodes and dependency path (why it was blocked).

## dbt integration (future)

- Store dbt manifest (models + depends_on) per project/workspace version.
- On breaking drift, map changed columns to impacted dbt models and skip them in scheduled runs.
- Add “schema drift gate” in dbt runner: refuse to run models that touch blocked datasets or blocked columns.

## Notification integrations

- Introduce a notifier interface with pluggable backends (Slack, PagerDuty, email).
- Config-driven routing: per tenant/project channel selection (engineering vs operations).
- Rate limiting + deduplication windows to avoid alert storms during repeated runs.
- Alert payload improvements: include dataset list affected, last successful run, and run/job links.

## Drift review workflow

- Replace simple “clear block” with explicit review state:
  - `detected -> acknowledged -> approved -> cleared`
- Require reviewer identity and reason; write to `audit_events`.
- Optional: attach remediation notes and mapping updates.

## Schema signature fidelity

- Capture additional attributes:
  - default values, computed columns
  - primary keys, foreign keys, indexes
  - collation/charset where relevant
- Improve rename detection:
  - similarity heuristics (Levenshtein) gated by type match
  - “rename candidates” list in drift event instead of a single classification

## UI improvements

- Add dataset list/catalog badge for drift/blocked status.
- Add richer diff viewer (before/after schema table with highlights).
- Add filter “show only drifted / blocked datasets” in Data Studio.

## Operational hardening

- Backfill signatures for existing connections/datasets on upgrade.
- Handle “first seen” signatures: record baseline without drift when no prior signature exists.
- Make drift checks efficient for large schemas (hash-first short-circuit).

