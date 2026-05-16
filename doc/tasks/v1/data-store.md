# Data Store Module Tasks

## Goal

Deliver the application persistence model for auth, snapshots, ontology,
analytics, anomalies, insights, and refresh metadata with clear schema
ownership and query boundaries.

## Tasks

- [ ] Define migration plan for `users`, `refresh_jobs`, and `data_snapshots`.
- [ ] Define migration plan for source snapshot tables.
- [ ] Define migration plan for ontology tables.
- [ ] Define migration plan for analytics tables.
- [ ] Define migration plan for anomaly tables.
- [ ] Define migration plan for insight cache tables.
- [ ] Add indexes required for snapshot lookups, monthly aggregation reads, and dashboard queries.
- [ ] Document repository ownership per table family to avoid cross-module write sprawl.
- [ ] Add seed or fixture strategy for local development and automated tests.
- [ ] Validate decimal-safe storage for money values and normalized month/date fields.

## Testing

- [ ] Add migration tests or schema verification checks for required tables and columns.
- [ ] Add repository integration tests for each table family.
- [ ] Add test fixtures that support unit, service, and integration layers without requiring a full production-sized dataset.
