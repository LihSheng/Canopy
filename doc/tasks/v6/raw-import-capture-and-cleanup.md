# Raw Import Capture And Cleanup

## Goal

Keep the original import artifact available long enough to support lineage, retry, and cleanup behavior.

## Tasks

- [ ] Persist the raw import artifact before cleaning.
- [ ] Store source metadata needed to identify the imported object later.
- [ ] Clean up discarded uploads when the user resets the setup flow.
- [ ] Keep raw artifact handling isolated from the cleaned dataset version.

## Testing

- [ ] Verify raw artifact persistence.
- [ ] Verify setup reset deletes discarded upload files.
- [ ] Verify raw and cleaned artifacts are kept separate.

