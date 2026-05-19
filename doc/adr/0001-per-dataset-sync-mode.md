# 0001 - Per-Dataset Sync Mode

Each Dataset carries its own `sync_mode` (batch, real_time, direct_query) and optional
`batch_strategy` (full_snapshot, incremental_cursor) with an auto-detected `cursor_column`.
This was chosen over connection-wide inheritance because the user's mental model is
per-table sync configuration — one Postgres connection can have `order_history` on
incremental cursor, `product_categories` on full snapshot, and `employee_salaries` as
a direct query with no copy at all.

## Status

Accepted.

## Considered Options

1. **Connection-wide default with per-dataset overrides** — faster to configure for
   homogeneous connections but adds inheritance complexity and violates the user's
   expectation of per-table control visible in the connection wizard.

2. **One global refresh schedule** — simpler orchestration but prevents the value
   proposition (reduced database load for large tables via incremental cursor).

3. **Per-dataset sync mode (chosen)** — each Dataset record owns its sync configuration.
   The refresh job still runs on one global schedule; during the source sync phase,
   each dataset's reader inspects its sync mode and builds the appropriate query
   (SELECT * for full snapshot, WHERE cursor_col > last_cursor for incremental,
   or skip entirely for direct_query).

## Consequences

- The `Dataset` domain gains `sync_mode`, `batch_strategy`, `last_cursor_value`, and
  `cursor_column` fields. These are nullable; null `sync_mode` implies the system
  default (batch / full snapshot).
- Direct Query datasets are never pulled by the refresh pipeline. They will live in
  a separate "Live Explorer" module that queries the source DB directly at request
  time. This preserves the snapshot consistency rule (ARCHITECTURE.md Rule 3) for
  dashboard, export, and AI flows.
- Real-Time is a domain value today with accelerated polling as the runtime
  implementation. The schema is ready for a future CDC/streaming pipeline swap
  without a migration.
- The cursor column is auto-detected from `INFORMATION_SCHEMA.COLUMNS` using a
  priority list of known names (`updated_at`, `last_modified_at`, etc.). Users
  can override it in the connection wizard. If the column changes post-config,
  the system resets `last_cursor_value` and forces a full re-pull.
