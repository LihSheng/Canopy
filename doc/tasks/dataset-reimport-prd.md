## Problem Statement

Users are currently unable to update an existing dataset with new data while maintaining version history. Every new data import currently creates a separate, new dataset instead of a new version of the existing one, leading to fragmentation and loss of lineage.

## Solution

Implement a re-import feature that allows users to upload new data files to an existing dataset. This feature will create a new immutable dataset version. The system will automatically activate valid new versions and move the previous version to a superseded state, while handling schema validation and error reporting.

## User Stories

1. As a dataset owner, I want to upload a new data file to an existing dataset, so that I can update the data without losing the dataset's history.
2. As a dataset owner, I want the system to automatically activate a new, valid version, so that my reports and analysis immediately use the most recent data.
3. As a dataset owner, I want the system to preserve previous versions, so that I can inspect or revert to them if needed.
4. As a dataset owner, I want the system to detect and reject imports that have missing mapped columns, so that I can prevent breaking my existing analysis or reports.
5. As a dataset owner, I want to see a clear error message when an import fails, so that I can correct the data file and try again.
6. As a dataset owner, I want the system to record failed import attempts as "Invalid Versions", so that I have a log of why my updates were rejected.

## Implementation Decisions

- **UI Location**: An "Upload New Version" button will be added to the "Versions" tab in the Dataset Workspace.
- **Workflow**: 
    - File upload initiates ingestion.
    - System validates mapped columns against the current Active Version.
    - If valid: New Dataset Version record is created, set as active, previous active version becomes superseded.
    - If invalid: Invalid Version record is created with failure reason, no changes to active version.
- **Backend**: New API endpoint to accept `dataset_id` and file for re-import.
- **Service**: Logic update to `DatasetVersionService` to handle activation and invalidation.

## Testing Decisions

- Tests will focus on external behavior: ensuring the active version updates correctly on success and that failed imports do not alter the active version.
- Existing tests for `DatasetVersionService` provide a strong foundation.
- We will add unit tests for schema validation and version transition logic.

## Out of Scope

- Automated data transformation or schema mapping (only strict validation for mapped columns will be performed).
- UI for editing or manually fixing invalid versions.
- Automated upstream system decommissioning.

## Further Notes

- The implementation will adhere to the definitions in `CONTEXT.md` regarding Datasets, Versions, and Active/Superseded/Invalid states.
