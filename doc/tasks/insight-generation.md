# Insight Generation Module Tasks

## Goal

Deliver grounded AI summaries from structured facts, with explicit fallback and
testable seams around prompt building and model invocation.

## Tasks

- [x] Define insight input fact model and output summary model.
- [x] Implement summary fact extraction from dashboard aggregates and anomalies.
- [x] Implement prompt/input builder for the LLM provider.
- [x] Implement LLM client gateway behind an interface.
- [x] Implement response parser and output normalizer.
- [x] Implement deterministic fallback summary builder.
- [x] Implement insight persistence to `generated_insights`.
- [x] Attach provenance metadata including snapshot id, generation time, and fallback flag.
- [x] Ensure the insight path never queries raw source rows directly.

## Testing

- [x] Add backend unit tests for fact extraction.
- [x] Add backend unit tests for prompt/input builder shape.
- [x] Add backend unit tests for fallback summary generation.
- [x] Add backend unit tests for response parsing.
- [x] Add backend service tests with mocked LLM client for success and failure paths.
- [x] Add backend integration tests for insight persistence and snapshot alignment.
