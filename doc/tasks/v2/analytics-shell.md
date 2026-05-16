# Analytics Shell Module Tasks

## Goal

Deliver the shared analytics shell with sidebar navigation, lightweight page
header, responsive drawer behavior, and bottom utility zone.

## Tasks

- [x] Create `analytics-shell` component boundary separate from page modules.
- [x] Create shared sidebar component with `Dashboard`, `Anomalies`, `Departments`, and `Reports` items.
- [x] Create brand block with top-mounted collapse toggle.
- [x] Create bottom utility zone with `Profile` and `Logout`.
- [x] Create active-item filled state aligned to `DESIGN.md`.
- [x] Create icon-rail collapsed mode with tooltips only.
- [x] Create responsive overlay drawer variant for smaller screens.
- [x] Create lightweight page header component with title, optional context text, and actions slot.
- [x] Create breadcrumb component used only on nested/detail pages.
- [x] Keep shell state limited to collapse and drawer behavior.
- [x] Persist collapse preference per browser if straightforward.

## Testing

- [x] Add unit tests for sidebar active-state rendering.
- [x] Add unit tests for collapse and expand behavior.
- [x] Add unit tests for drawer open and close behavior.
- [x] Add integration test proving shell stays stable across top-level page navigation.
