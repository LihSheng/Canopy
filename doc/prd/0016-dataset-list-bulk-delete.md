# PRD: Dataset List Bulk Delete

Status: draft

## Problem Statement

The current dataset deletion flow is too slow for users who need to clean up
multiple datasets. Today, deletion happens one dataset at a time from the
dataset detail workspace, which forces the user to open each dataset, review
its delete state, and confirm deletion repeatedly.

That flow is workable for rare single-item cleanup, but it is inefficient for
routine list management. The user needs a faster way to remove multiple
datasets from the dataset list without losing visibility into delete blockers.

The product must also stay safe:

- blocked datasets must not disappear from the selection flow without an
  explanation
- users should still be able to select blocked datasets, so they can understand
  what will happen
- the existing dataset detail single-delete action should remain available as a
  fallback

## Solution

Add bulk delete to the dataset list page.

The list should support:

- row checkboxes for individual dataset selection
- a header checkbox that selects the current page only
- a bulk action bar that appears when one or more rows are selected
- a `Delete selected` action for the selected page items
- a confirmation dialog that shows which datasets will be deleted and which
  will be skipped
- skipped rows shown with explicit block reasons before the user confirms

Bulk delete should work on the current page only. The detail page should keep
its single-delete button unchanged.

The delete experience should be transparent:

- allowed datasets are deleted
- blocked datasets stay selected and are listed as skipped
- skipped reasons are visible before confirmation
- the final result summarizes what was deleted and what was skipped

## User Stories

1. As a dataset manager, I want to select multiple datasets from the list, so
   that I can clean up faster.
2. As a dataset manager, I want a bulk delete action to appear when I select
   rows, so that the action is available only when needed.
3. As a dataset manager, I want the header checkbox to select the current page
   only, so that I do not accidentally act on a larger set than I can see.
4. As a dataset manager, I want blocked datasets to remain selectable, so that
   I can see exactly which datasets cannot be removed yet.
5. As a dataset manager, I want to see block reasons before I confirm deletion,
   so that I understand the outcome ahead of time.
6. As a dataset manager, I want the confirmation dialog to separate deletable
   rows from skipped rows, so that I can review the action before committing.
7. As a dataset manager, I want the system to delete the allowed datasets and
   skip the blocked ones, so that one bad row does not stop the whole cleanup.
8. As a dataset manager, I want the result summary to tell me what happened,
   so that I can trust the bulk action outcome.
9. As a dataset manager, I want the dataset detail page to keep its current
   single-delete action, so that I still have a focused fallback for one-off
   cleanup.
10. As a platform operator, I want bulk delete to reuse the existing delete
    dependency checks, so that delete safety stays consistent across the app.
11. As a platform operator, I want selection state to stay page-scoped, so that
    the UI stays predictable and easy to test.
12. As a platform operator, I want blocked datasets to remain visible in the
    bulk flow, so that users do not lose the context for skipped items.
13. As a platform operator, I want the delete flow to remain explicit about
    what is deleted and what is skipped, so that the UI does not hide partial
    success.
14. As a product owner, I want the list page to feel like the primary cleanup
    surface, so that users do not need to drill into each dataset individually.

## Implementation Decisions

- Add row selection to the dataset list table.
- Add a bulk action bar that appears once the selection is non-empty.
- Make the header checkbox select only the current page.
- Keep the dataset detail single-delete action unchanged.
- Use the existing per-dataset dependency summary to determine whether a row
  can be deleted.
- Allow blocked datasets to stay selected.
- Show block reasons in the confirmation dialog before the user confirms.
- Delete only the allowed rows on confirm.
- Return a clear per-row result summary after the action completes.
- Keep the delete safety rules consistent with the existing single-delete
  behavior.
- Keep the implementation modular:
  - dataset list selection and bulk action state in the list page component
  - row action rendering in the shared table surface
  - delete eligibility and block reason handling through the existing dataset
    delete summary contract
  - deletion execution through the existing dataset delete endpoint unless a
    dedicated batch endpoint is later needed
- Keep the bulk delete behavior scoped to the dataset list, not the dataset
  detail workspace.

## Testing Decisions

- Good tests verify external behavior, not table internals or hidden state.
- The list page should be tested for:
  - checkbox rendering
  - current-page select-all behavior
  - bulk action bar visibility
  - mixed allowed and blocked selection
  - pre-confirmation skipped-row explanations
  - result summary after confirm
- The detail page should keep its existing single-delete regression coverage.
- The delete flow should be tested with:
  - rows that can delete
  - rows that are blocked
  - mixed selections
  - empty selections
- Modules to test:
  - dataset list selection and bulk action flow
  - dataset delete summary aggregation
  - delete confirmation and result summary UI
  - existing single-delete detail flow
- Prior art:
  - existing dataset detail delete tests
  - existing dataset list rendering tests
  - existing confirmation dialog and table component tests

## Out of Scope

- Bulk delete from dataset detail
- Cross-page or whole-tenant select-all
- Permanent destructive delete of blocked datasets
- New retention or governance policy logic
- Changing the meaning of existing delete dependency checks
- Row-level mass actions other than delete
- Background purge workflows

## Further Notes

This is a UX cleanup feature, not a new data model feature.

The intended interaction model is:

1. user selects rows on the dataset list page
2. the bulk action bar appears
3. user clicks `Delete selected`
4. dialog shows deletable rows and skipped rows with reasons
5. user confirms
6. allowed rows delete, blocked rows remain, summary is shown

The safest default is to keep the action local to the current page and keep
single-delete available in the detail workspace.
