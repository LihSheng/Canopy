# Deterministic Cleaning Pipeline

## Goal

Transform imported data with predictable, explainable cleaning rules before version creation.

## Tasks

- [ ] Trim whitespace from imported values.
- [ ] Normalize column headers.
- [ ] Infer basic value types.
- [ ] Remove fully empty rows.
- [ ] Flag invalid cells as structured issues.
- [ ] Keep cleaning free of AI and business-rule enrichment.

## Testing

- [ ] Verify whitespace trimming and header normalization.
- [ ] Verify empty-row removal.
- [ ] Verify type inference falls back safely.
- [ ] Verify invalid-cell flagging.

