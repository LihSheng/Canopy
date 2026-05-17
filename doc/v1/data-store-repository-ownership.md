# Data Store — Repository Ownership

Each table family is written by exactly one repository module.
Reads may cross boundaries through the AnalyticsRepository or direct queries.

## Ownership Map

| Logical Zone | Table(s) | Owner | Repository Class | Write Operations |
|---|---|---|---|---|
| **Auth** | `users` | `auth` | `AuthRepository` (`auth/repository.py`) | `create()`, `update_last_login()` |
| **Source Snapshot** | `source_snapshots`, `source_snapshot_rows` | `sync` | `SnapshotRepository` (`sync/repositories/snapshot.py`) | `save_snapshot()`, `save_rows()` |
| **Ontology** | `departments`, `employees`, `cost_centers`, `budget_codes`, `expense_claims`, `payroll_expenses`, `unresolved_mapping_issues` | `ontology` | `OntologyRepository` (`ontology/repositories/ontology.py`) | `save_all()`, `save_*()` per entity |
| **Analytics** | `analytics_monthly_department_spend`, `analytics_monthly_employee_spend`, `analytics_monthly_claim_type_spend`, `analytics_dashboard_summary_cache` | `analytics` | `AnalyticsRepository` (`analytics/repositories/analytics.py`) | `save_department_spends()`, `save_employee_spends()`, `save_claim_type_spends()`, `save_summary_cache()` |
| **Anomalies** | `detected_anomalies` | `anomalies` | `AnomalyRepository` (`anomalies/repository.py`) | `save_anomalies()`, `save_many()` |
| **Insights** | `generated_insights` | `insights` | `InsightRepository` (`insights/repository.py`) | `save()` |
| **Refresh / Jobs** | `refresh_jobs`, `data_snapshots` | `refresh` | `RefreshRepository` (`refresh/repository.py`) | `save_job()`, `update_job()`, `mark_current_snapshot()` |

## Rules

1. **No cross-module writes.** A module must not write to a table owned by another module. Any write to `users` comes only from `auth`, any write to `departments` only from `ontology`, etc.

2. **Reads are permissive.** Cross-module reads are expected. For example, `analytics/service.py` joins across `analytics_monthly_*`, `ontology.*`, and `auth.*` tables to build dashboard responses. This is allowed via the shared `db: Session`.

3. **Clear-snapshot operations are owned by the zone.** Each repository that stores snapshot-scoped data provides a `clear_snapshot(snapshot_id)` call used by the aggregation pipeline to replace stale data.

4. **No direct ORM model access outside the owning module.** If a module needs to read data owned by another zone, it should use the owner's repository class or a shared query helper — not direct model queries outside of controlled join contexts (e.g., AnalyticsRepository joins ExpenseClaimModel).

## Snapshot Isolation

All analytics, anomaly, insight, and ontology tables are scoped to `snapshot_id`. Refresh orchestration owns the snapshot lifecycle:
- `SyncOrchestrator` produces the snapshot
- `OntologyOrchestrator` writes ontology records
- `run_aggregation_pipeline` replaces analytics for the snapshot
- `detect_anomalies` replaces anomalies for the snapshot
- `generate_insight` replaces insights for the snapshot
- `RefreshRepository.mark_current_snapshot` activates the new snapshot

This sequence ensures the same `snapshot_id` keys all derived data for the dashboard, export, and AI summary.
