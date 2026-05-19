# Dataset Workspace Delete Actions PRD

## Problem Statement

Users need a safe way to remove dummy imports and test data from the Dataset Workspace without breaking downstream usage. Right now, the delete intent is ambiguous because the same imported source can exist as a data connection, a logical dataset, and multiple re-import versions. The product needs to make it obvious what is being deleted and must block deletion when something downstream still depends on it.

## Solution

Add explicit delete actions to the Dataset Workspace:

- `Delete Dataset` in the workspace header for removing the whole logical dataset group
- `Delete Version` in the Versions tab for removing one imported snapshot

Deletion is allowed only when dependency checks confirm that no active downstream dataset, run, or modeled asset still depends on the target. The system deletes app-owned records only. It does not delete the upstream source system or external file location.

## User Stories

1. As a data user, I want to delete a dummy imported dataset, so that I can clean up test data from the workspace.
2. As a data user, I want to delete one bad import version, so that I can keep the newer corrected versions.
3. As a data user, I want the delete action to name the exact target, so that I do not accidentally delete the wrong object.
4. As a data user, I want to see dependency warnings before deletion, so that I know why delete is blocked.
5. As a data user, I want delete to be blocked when downstream assets still use the data, so that I do not break reports or modeled outputs.
6. As a data user, I want dataset delete to remove the whole logical dataset group, so that stale imports disappear completely when they are no longer needed.
7. As a data user, I want version delete to remove only one snapshot, so that I can preserve valid history when only one import is wrong.
8. As a data user, I want re-imports to create newer versions under the same dataset, so that version history remains grouped correctly.
9. As a data user, I want the workspace to show the active version clearly, so that I know which version is currently being used.
10. As a data user, I want the delete flow to confirm my action, so that I can cancel if I clicked by mistake.
11. As an administrator, I want deletion to follow lineage rules, so that the platform remains safe and explainable.
12. As an administrator, I want the system to delete only app-owned records, so that the product does not attempt to modify upstream source systems.

## Implementation Decisions

- The Dataset Workspace will expose two destructive actions with different scopes: dataset delete and version delete.
- `Delete Dataset` removes the logical dataset group and its versions only when dependency checks pass.
- `Delete Version` removes a single imported version only when it is not the active version and no dependency blocks exist.
- The system will compute a dependency summary before allowing deletion.
- The dependency summary must cover at least active datasets, active or queued runs, and other modeled downstream usage.
- The UI must show the dependency summary and explain why deletion is blocked.
- The UI must use explicit labels instead of a generic `Delete` button.
- The delete operations are limited to app-owned records; they do not delete the upstream source system.
- Re-imports continue to create newer versions under the same logical dataset identity.
- The underlying data model must distinguish connection identity, dataset identity, version identity, and import run identity so the UI can reason about same source versus newer version.

## Testing Decisions

- Add backend integration tests for allowed dataset deletion when unused.
- Add backend integration tests for blocked dataset deletion when dependencies exist.
- Add backend integration tests for allowed version deletion when the version is removable.
- Add backend integration tests for blocked version deletion when the version is active or referenced.
- Add frontend integration tests for the correct button placement and labels in the Dataset Workspace.
- Add frontend integration tests for the dependency warning and blocked-delete state.
- Tests should verify external behavior only: visible labels, blocked or allowed outcomes, and dependency messaging.

## Out of Scope

- Deleting the upstream source system or external file storage.
- MySQL connector implementation.
- Cleaning rules beyond the delete dependency checks.
- Full visualization redesign.
- Ontology editing workflows.
- Cross-dataset governance workflows outside the current workspace.

## Further Notes

The user intent is cleanup, not destruction of source truth. The delete split exists because a logical dataset can have many re-import versions, and each version may have a different downstream dependency state. The workspace should therefore make the target explicit:

- Dataset scope: remove the whole logical imported object
- Version scope: remove only one import snapshot

This preserves lineage clarity while still giving the user a practical way to remove dummy test data.
