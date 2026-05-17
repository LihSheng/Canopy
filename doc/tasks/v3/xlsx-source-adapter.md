# Excel Source Adapter

## Goal

Parse Excel workbooks reliably and convert them into the generic source shape
consumed by profiling and cleaning.

## Tasks

- [ ] Parse workbook sheets and rows from the stored file.
- [ ] Preserve raw cell values where needed for lineage and replay.
- [ ] Handle empty sheets, merged cells, and alternate header rows.
- [ ] Emit a generic workbook data structure to the profiler.
- [ ] Keep Excel-specific logic inside the adapter boundary.

## Testing

- [ ] Add unit tests for sheet parsing and row extraction.
- [ ] Add unit tests for edge cases such as hidden sheets and multi-row headers.

