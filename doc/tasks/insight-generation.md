# Insight Generation Module Tasks

## Goal

Deliver grounded AI summaries from structured facts, with explicit fallback and
testable seams around prompt building and model invocation.

## Tasks

- [ ] Define insight input fact model and output summary model.
- [ ] Implement summary fact extraction from dashboard aggregates and anomalies.
- [ ] Implement prompt/input builder for the LLM provider.
- [ ] Implement LLM client gateway behind an interface.
- [ ] Implement response parser and output normalizer.
- [ ] Implement deterministic fallback summary builder.
- [ ] Implement insight persistence to `generated_insights`.
- [ ] Attach provenance metadata including snapshot id, generation time, and fallback flag.
- [ ] Ensure the insight path never queries raw source rows directly.

## Testing

- [ ] Add backend unit tests for fact extraction.
- [ ] Add backend unit tests for prompt/input builder shape.
- [ ] Add backend unit tests for fallback summary generation.
- [ ] Add backend unit tests for response parsing.
- [ ] Add backend service tests with mocked LLM client for success and failure paths.
- [ ] Add backend integration tests for insight persistence and snapshot alignment.
