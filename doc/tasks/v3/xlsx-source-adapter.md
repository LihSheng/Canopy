# Excel Source Adapter

## Goal

Parse Excel workbooks reliably and convert them into the generic source shape
consumed by profiling and cleaning.

## Tasks

- [x] Parse workbook sheets and rows from the stored file.
- [x] Preserve raw cell values where needed for lineage and replay.
- [x] Handle empty sheets, merged cells, and alternate header rows.
- [x] Emit a generic workbook data structure to the profiler.
- [x] Keep Excel-specific logic inside the adapter boundary.

## Testing

- [x] Add unit tests for sheet parsing and row extraction.
- [x] Add unit tests for edge cases such as hidden sheets and multi-row headers.

