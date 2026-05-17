# Dataset Preview Grid

## Goal

Replace the simple preview table with a scalable read-only dataset grid.

Product requirement:

- [`doc/v4/reusable-data-table-prd.md`](../../v4/reusable-data-table-prd.md)

## Tasks

- [x] Add `glide-data-grid` dependency after license/security review.
  - **Decision (2026-05-17):** `@glideapps/glide-data-grid` is installed with npm peer
    resolution override because the published peer range still caps React at 18.x, while this
    app is on React 19.2.4. The Glide canvas grid is now used for dataset preview.
    `PreviewGrid` remains only for the setup wizard static-file preview.
- [x] Build read-only preview grid component.
  - Implemented as `DatasetPreviewGrid` in `src/components/v4/dataset-preview-grid.tsx`.
  - Uses `glide-data-grid` with read-only text cells, row numbering with page offset, NULL
    display, and the existing search input / pagination shell.
  - Includes filtered row count badge and summary footer ("Showing X--Y of Z rows").
  - States covered: loading (`LoadingSpinner`), error (`ErrorState` with retry), empty
    (`EmptyState`), empty search results with hint.
- [x] Map dataset preview API data into grid rows and columns.
  - `fetchDatasetPreview` updated to accept `{ page, page_size, search }` params.
  - `DatasetPreviewResponse` type defined in `src/lib/api/data-source.ts`.
  - Backend `preview_service.read_dataset_preview` returns full metadata including
    `filtered_row_count`, `page`, `page_size`.
  - `dataset-workspace-content.tsx` wired with separate preview state management
    (`previewPage`, `previewSearch`, `previewLoading`, `previewError`).
  - Search resets page to 1 on change.
- [x] Add column scanning and compact metadata display.
  - Schema tab in workspace still renders column names from preview.
  - Health panel displays row/column counts.
- [x] Preserve read-only behavior.
  - Grid cells are plain text display in `<td>` elements, no inputs or contentEditable.
  - No cell editing callbacks.
  - Backend returns JSONL data read-only (no write path).

## Testing

- [x] Add frontend tests for grid rendering.
  - 11 tests in `src/tests/unit/dataset-preview-grid.test.tsx`.
  - Covers: renders columns/rows, row numbers, loading state, error state, empty state
    (no columns, no rows after search), search input callback, pagination callback,
    disabled previous/next buttons, filtered count badge, NULL values.
- [x] Add interaction tests confirming cells are not editable.
  - Grid cells are emitted as read-only `GridCellKind.Text` values with `allowOverlay: false`
    and `readonly: true`.
  - Verified via rendering tests that the grid adapter receives read-only cells and the NULL
    mapping.

## Backend enhancements (from `doc/tasks/v4/dataset-preview-grid.md` implementation)

- [x] `v4/dataset/preview_service.py` -- `read_dataset_preview()` with full-file search and pagination.
  - Search scans entire JSONL file (not just first page).
  - Returns `columns`, `rows`, `total_row_count`, `filtered_row_count`, `page`, `page_size`.
- [x] Route `GET /datasets/{id}/preview` updated with `page`, `page_size`, `search` query params.
- [x] 5 backend unit tests + 5 integration tests covering pagination, search, legacy hydration, invalid input.
- [x] Legacy `upload_id` and `source_file_path` hydration preserved.

## Shared table contract (from `doc/v4/reusable-data-table-prd.md`)

- [x] `src/components/shared/table/types.ts` -- `ColumnDef`, `TablePage`, `TableState`, `RowIdentity`.
- [x] `src/components/shared/table/compact-table.tsx` -- `CompactTable` with loading/empty/error/search/pagination support.
- [x] Dataset list (`dataset-list-content.tsx`) migrated to `CompactTable`.
- [x] 7 frontend tests for compact table in `src/tests/unit/compact-table.test.tsx`.
