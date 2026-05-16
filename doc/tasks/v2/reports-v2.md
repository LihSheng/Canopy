# Reports V2 Module Tasks

## Goal

Turn `Reports` into an export center with presets first, recent history second,
and consistent operational status handling.

## Tasks

- [ ] Create reports page container with no top summary strip.
- [ ] Create preset workspace for `Executive Summary`, `Department Spend`, and `Anomaly Review`.
- [ ] Create recent export history list.
- [ ] Create history row state handling for queued, running, completed, and failed exports.
- [ ] Show source context on each row using preset name, time range, and snapshot timestamp.
- [ ] Expose `Download` and `Run again` on completed rows.
- [ ] Expose clean failure summary plus optional detail view on failed rows.
- [ ] Keep exports manual-only in v2; do not add scheduling UI.

## Testing

- [ ] Add unit tests for reports workspace mapper.
- [ ] Add unit tests for export-history row rendering across statuses.
- [ ] Add integration test for preset-triggered export creation.
- [ ] Add integration test for `Run again` flow on a completed export.
