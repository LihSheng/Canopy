# Anomaly Detection Module Tasks

## Goal

Deliver deterministic, explainable anomaly rules with per-rule isolation and a
single coordinator that stores anomaly facts for UI and insight generation.

## Tasks

- [x] Define anomaly domain types and severity types.
- [x] Define anomaly rule interface.
- [x] Implement month-over-month department total spend spike rule.
- [x] Implement month-over-month department claim spend spike rule.
- [x] Implement historical outlier rule if retained for v1.
- [x] Implement severity classification logic behind config-driven thresholds.
- [x] Implement anomaly coordinator service for one snapshot.
- [x] Persist anomaly outputs to `detected_anomalies`.
- [x] Expose drill-down support keys and driver payload structure consistently across rules.

## Testing

- [x] Add backend unit tests for each anomaly rule independently.
- [x] Add backend unit tests for severity classification thresholds.
- [x] Add backend unit tests for anomaly coordinator merge behavior.
- [x] Add backend integration tests for anomaly persistence and read queries.
