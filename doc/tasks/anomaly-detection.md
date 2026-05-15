# Anomaly Detection Module Tasks

## Goal

Deliver deterministic, explainable anomaly rules with per-rule isolation and a
single coordinator that stores anomaly facts for UI and insight generation.

## Tasks

- [ ] Define anomaly domain types and severity types.
- [ ] Define anomaly rule interface.
- [ ] Implement month-over-month department total spend spike rule.
- [ ] Implement month-over-month department claim spend spike rule.
- [ ] Implement historical outlier rule if retained for v1.
- [ ] Implement severity classification logic behind config-driven thresholds.
- [ ] Implement anomaly coordinator service for one snapshot.
- [ ] Persist anomaly outputs to `detected_anomalies`.
- [ ] Expose drill-down support keys and driver payload structure consistently across rules.

## Testing

- [ ] Add backend unit tests for each anomaly rule independently.
- [ ] Add backend unit tests for severity classification thresholds.
- [ ] Add backend unit tests for anomaly coordinator merge behavior.
- [ ] Add backend integration tests for anomaly persistence and read queries.
