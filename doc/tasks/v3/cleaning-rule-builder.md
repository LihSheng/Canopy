# Cleaning Rule Builder

## Goal

Provide a visual rule editor that creates deterministic transformation steps
without requiring code from non-technical users.

## Tasks

- [x] Model cleaning steps as an ordered rule stack.
- [x] Support draft state for editing.
- [x] Support published state for executable versions.
- [x] Implement step creation, reordering, and parameter editing.
- [x] Include basic rule families for trimming, casting, renaming, parsing,
  deduping, and null normalization.
- [x] Store the generated pipeline spec as structured data.

## Testing

- [x] Add frontend tests for step editing and reordering.
- [x] Add backend tests for pipeline spec serialization.
- [x] Add unit tests for supported rule validation.

