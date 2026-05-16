# Anomalies V2 Module Tasks

## Goal

Turn `Anomalies` into a triage workspace with severity grouping, direct
filters, and clean drill-down into department detail.

## Tasks

- [ ] Create anomalies page container with no top summary strip.
- [ ] Create filter bar with time range, severity, and sort controls as designed.
- [ ] Group anomaly rows by severity.
- [ ] Keep `High` expanded by default and `Medium` / `Low` collapsed initially.
- [ ] Create compact anomaly row with department, severity, change %, and one-line reason.
- [ ] Route anomaly row click to department detail.
- [ ] Keep workflow read-only: no reviewed, dismissed, or triage-state mutation in v2.

## Testing

- [ ] Add unit tests for grouped anomaly-list mapper.
- [ ] Add unit tests for expand and collapse behavior by severity group.
- [ ] Add integration test for anomalies page loading with department prefilter.
- [ ] Add integration test for anomaly-row click to department detail.
