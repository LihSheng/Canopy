# Workbook Profiling And Preview

## Goal

Inspect uploaded workbooks, identify the most likely data sheet, infer column
types, and generate the preview model used by the review UI.

## Tasks

- [x] Implement sheet enumeration and candidate scoring.
- [x] Detect likely header rows and empty or hidden sheets.
- [x] Infer column data types from sampled rows.
- [x] Generate column confidence and mapping suggestions.
- [x] Build the workbook preview read model.
- [x] Surface warnings for ambiguous structure or low-confidence columns.
- [x] Expose preview data through a dedicated API endpoint.

## Testing

- [x] Add unit tests for sheet scoring heuristics.
- [x] Add unit tests for type inference and confidence scoring.
- [x] Add integration tests for preview generation from stored files.

