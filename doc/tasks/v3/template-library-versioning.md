# Template Library And Versioning

## Goal

Manage reusable cleaning templates by dataset type and source profile with a
draft and published lifecycle.

## Tasks

- [x] Create template family records keyed by dataset type and source profile.
- [x] Add draft and published template states.
- [x] Create immutable published versions with version numbers.
- [x] Allow cloning from an existing template or version.
- [x] Bind each upload to one specific published template version.
- [x] Expose template history and version selection in the UI.

## Testing

- [x] Add backend tests for draft-to-published transitions.
- [x] Add backend tests for version binding on uploads.
- [x] Add integration tests for template cloning and reuse.

