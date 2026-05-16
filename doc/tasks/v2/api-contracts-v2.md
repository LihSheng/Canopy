# API Contracts V2 Module Tasks

## Goal

Provide the backend read models and route contracts required by the v2 shell
and page flows without violating existing architecture boundaries.

## Tasks

- [ ] Define or update dashboard command-view response contract.
- [ ] Define or update anomalies list contract to support time range and department prefilter.
- [ ] Define or update departments ranking contract for default attention sort and time range.
- [ ] Define or update department detail contract for summary, trend, AI summary, and contributor split data.
- [ ] Define or update reports history contract to include preset, status, time range, and snapshot timestamp.
- [ ] Define export rerun contract.
- [ ] Define compact refresh-status contract for header drawer behavior.
- [ ] Keep route handlers thin and move read-model shaping into services or dedicated mappers.

## Testing

- [ ] Add backend unit tests for dashboard command-view assembler.
- [ ] Add backend unit tests for anomaly grouping and ranking read-model mappers.
- [ ] Add backend unit tests for department detail assembler.
- [ ] Add backend unit tests for export-history summary mapper.
- [ ] Add backend integration tests for v2 read routes and export rerun route.
