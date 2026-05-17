# PRD: Reusable Data Table Component

## Problem Statement

HERD Aggregator currently renders tables with several one-off components. The
dataset preview grid, dataset list, run history, dashboard drill-down tables,
and schema table each own their own table markup and behavior.

This creates an inconsistent user experience and makes every table feature
expensive to add. Search, filtering, pagination, column sizing, loading states,
empty states, and read-only enforcement would need to be rebuilt per table.

The immediate user-visible pain is the dataset preview page. Users expect the
preview to behave like a working data surface, but the current table only shows
static rows. It does not support search, filtering, pagination, sorting, or
spreadsheet-like navigation.

The broader product need is a standard table component that every data table in
the system can use, while still respecting the v4 direction: read-only dataset
assets, immutable dataset versions, and a quiet operational workspace.

## Solution

Build a reusable data table component family for HERD Aggregator.

The component should become the standard table surface for all product tables.
It should support two main use cases:

- data-grid tables for large, scrollable, spreadsheet-like datasets
- compact record tables for lists, run history, and dashboard drill-downs

Dataset preview should use the data-grid mode first because v4 already
recommends `glide-data-grid` for preview grids. Other product tables should
migrate to the shared component progressively.

The shared table should provide consistent:

- search
- filtering
- pagination or virtual scrolling
- sorting
- loading state
- empty state
- error state
- column definitions
- row identity
- read-only behavior
- responsive sizing
- consistent visual styling

Search and filtering for dataset preview should apply to the full dataset
version, not only the first preview slice. This prevents users from searching
for rows that exist but are absent from the currently loaded preview window.

## User Stories

1. As an executive user, I want tables to behave consistently across the app, so that I do not need to relearn each page.
2. As an executive user, I want to search table rows, so that I can quickly find a department, employee, run, or dataset.
3. As an executive user, I want clear empty states, so that I know whether there is no data or the table is still loading.
4. As an executive user, I want readable pagination or scrolling, so that large tables do not overwhelm the page.
5. As an executive user, I want tables to keep the same visual style, so that the application feels like one system.
6. As a semi-technical user, I want dataset preview to look and feel like a spreadsheet, so that uploaded files are easier to inspect.
7. As a semi-technical user, I want dataset preview to remain read-only, so that I cannot accidentally mutate source data.
8. As a semi-technical user, I want to search across the full dataset version, so that I can trust the search result.
9. As a semi-technical user, I want to filter dataset preview rows, so that I can inspect only records matching specific values.
10. As a semi-technical user, I want sortable columns, so that I can quickly identify high, low, or unusual values.
11. As a semi-technical user, I want column widths to be adjustable or sensible by default, so that long values remain inspectable.
12. As a semi-technical user, I want sticky headers, so that column context is preserved while scrolling.
13. As a semi-technical user, I want row numbers in dataset preview, so that I can refer to a visible row during review.
14. As a semi-technical user, I want table loading states to be visible, so that I know the system is processing my request.
15. As a semi-technical user, I want table errors to be visible and retryable, so that failed data loads are not silent.
16. As an admin user, I want dataset lists to use the same table pattern, so that dataset status and metadata are easier to scan.
17. As an admin user, I want run history to use the same table pattern, so that run status, duration, and output version are easier to compare.
18. As an admin user, I want schema tables to use the same table pattern, so that column metadata appears consistently.
19. As an admin user, I want filtering controls to be predictable, so that I can narrow operational views without guessing how each table works.
20. As a developer, I want one table API for common table behavior, so that search, filtering, loading, and empty states are not duplicated.
21. As a developer, I want table column definitions to be explicit, so that table behavior is testable and not scattered through JSX.
22. As a developer, I want a stable row identity contract, so that row selection, virtualization, and pagination remain reliable.
23. As a developer, I want backend-backed pagination for large dataset previews, so that the browser does not need to load entire datasets.
24. As a developer, I want backend-backed search for dataset preview, so that search results are correct across the full dataset version.
25. As a developer, I want compact tables and data-grid tables to share concepts but not force the same rendering engine, so that simple tables stay simple.
26. As a developer, I want tests around table behavior instead of implementation details, so that the table can evolve without brittle tests.
27. As a future connector developer, I want the table component to work for static files and future sources, so that MySQL, API, and Google Sheets previews can reuse the same surface.
28. As a product owner, I want table behavior documented in one PRD, so that future agents do not rebuild competing table systems.

## Implementation Decisions

- Build a shared table component family, not another page-specific preview table.
- Use the shared component for all product tables over time.
- Treat dataset preview as the first implementation target.
- Use `glide-data-grid` for spreadsheet-like dataset preview after license and security review.
- Keep compact record tables available for simple list-style use cases such as dataset list and run history.
- Do not expose cell editing in the first version.
- Keep dataset preview read-only.
- Add backend-backed preview pagination.
- Add backend-backed preview search.
- Prefer backend-backed filtering for dataset preview when filters must apply to the full dataset version.
- Allow frontend-only filtering only for small record tables whose full row set is already loaded.
- Preserve the existing frontend API adapter boundary. UI components should not call `fetch` directly.
- Add a typed table column definition interface that supports labels, value access, width hints, alignment, and optional filter metadata.
- Add a typed table data contract that separates rows, total row count, page state, search state, filter state, and loading/error state.
- For dataset preview, update the preview API to accept page, page size, search query, sort, and filter inputs.
- For dataset preview, update the preview API to return columns, rows, total row count, page metadata, and applied query metadata.
- Keep dataset version reads immutable. Search, sort, filter, and pagination must not mutate dataset versions.
- Keep table styling aligned with the analytics shell and v4 data workspace direction: dense, quiet, and operational.
- Avoid putting every table into a heavy grid if the table is only a small metadata list.
- Keep implementation modular: table rendering, table state, dataset preview API mapping, and page-level orchestration should be separate.

Suggested modules:

- Shared table foundation: owns common column definitions, states, toolbar layout, empty/loading/error handling, and visual conventions.
- Data-grid adapter: owns `glide-data-grid` integration and converts shared table contracts into grid-specific rendering.
- Compact table adapter: owns standard HTML table rendering for smaller record tables.
- Dataset preview read model: owns preview query state, API calls, and mapping backend responses into table rows.
- Dataset preview backend service: owns reading immutable dataset version files with pagination, search, sorting, and filtering.

## Testing Decisions

- Test external behavior, not implementation details.
- Frontend tests should verify visible outcomes: search input changes rows, pagination changes visible rows, loading appears, errors appear, empty states appear, and read-only cells cannot be edited.
- Backend tests should verify preview API behavior across full dataset versions, not only the first 100 rows.
- Backend tests should cover page and page size behavior.
- Backend tests should cover search returning matches outside the first page.
- Backend tests should cover empty search results.
- Backend tests should cover unsupported or invalid sort/filter fields.
- Backend tests should cover legacy static-file datasets that hydrate from old upload metadata.
- Component tests should cover compact table rendering with small fixed rows.
- Component tests should cover data-grid read-only behavior once `glide-data-grid` is introduced.
- API adapter tests should cover query parameter construction for search, filters, sort, and pagination.
- Prior frontend test examples include existing table rendering tests and setup-page workflow tests.
- Prior backend test examples include existing data-source importer and data-source API integration tests.

## Out of Scope

- Direct cell editing.
- Saving changes back to source systems.
- Bulk row actions.
- Row-level permissions.
- Enterprise spreadsheet formulas.
- Pivot tables.
- Charting inside table cells.
- Cross-dataset joins inside the table UI.
- Replacing every existing table in the first implementation slice.
- Full database indexing strategy for future large external sources.
- MySQL, PostgreSQL, REST API, or Google Sheets connector implementation.

## Further Notes

The PRD assumes “all tables use this component” means all product data tables
should go through the shared table component family. It does not require every
table to use `glide-data-grid`. Heavy grid behavior should be used where the
user is inspecting tabular data at scale. Simple operational lists can use the
compact adapter while still sharing the same table contract and visual states.

Open decision for implementation planning:

- Should the first slice include only dataset preview, or should it also migrate
  dataset list and run history immediately?

Recommended answer:

- First slice should include dataset preview plus one compact table migration.
  This proves both rendering modes and prevents the shared table abstraction
  from being shaped only by the dataset preview case.
