# Template Library And Versioning

## Goal

Manage reusable cleaning templates by dataset type and source profile with a
draft and published lifecycle.

## Tasks

- [ ] Create template family records keyed by dataset type and source profile.
- [ ] Add draft and published template states.
- [ ] Create immutable published versions with version numbers.
- [ ] Allow cloning from an existing template or version.
- [ ] Bind each upload to one specific published template version.
- [ ] Expose template history and version selection in the UI.

## Testing

- [ ] Add backend tests for draft-to-published transitions.
- [ ] Add backend tests for version binding on uploads.
- [ ] Add integration tests for template cloning and reuse.

