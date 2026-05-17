# Cleaning Rule Builder

## Goal

Provide a visual rule editor that creates deterministic transformation steps
without requiring code from non-technical users.

## Tasks

- [ ] Model cleaning steps as an ordered rule stack.
- [ ] Support draft state for editing.
- [ ] Support published state for executable versions.
- [ ] Implement step creation, reordering, and parameter editing.
- [ ] Include basic rule families for trimming, casting, renaming, parsing,
  deduping, and null normalization.
- [ ] Store the generated pipeline spec as structured data.

## Testing

- [ ] Add frontend tests for step editing and reordering.
- [ ] Add backend tests for pipeline spec serialization.
- [ ] Add unit tests for supported rule validation.

