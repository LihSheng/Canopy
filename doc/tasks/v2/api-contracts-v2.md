# API Contracts V2 Module Tasks

## Goal

Provide the backend read models and route contracts required by the v2 shell
and page flows without violating existing architecture boundaries.

## Tasks

- [x] Define or update dashboard command-view response contract.
- [x] Define or update anomalies list contract to support time range and department prefilter.
- [x] Define or update departments ranking contract for default attention sort and time range.
- [x] Define or update department detail contract for summary, trend, AI summary, and contributor split data.
- [x] Define or update reports history contract to include preset, status, time range, and snapshot timestamp.
- [x] Define export rerun contract.
- [x] Define compact refresh-status contract for header drawer behavior.
- [x] Keep route handlers thin and move read-model shaping into services or dedicated mappers.

## Testing

- [x] Add backend unit tests for dashboard command-view assembler.
- [x] Add backend unit tests for anomaly grouping and ranking read-model mappers.
- [x] Add backend unit tests for department detail assembler.
- [x] Add backend unit tests for export-history summary mapper.
- [x] Add backend integration tests for v2 read routes and export rerun route.
