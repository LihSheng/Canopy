Read `ARCHITECTURE.md` first. It is the source of truth.

Follow these rules:
- Keep the system read-only to the source system.
- Use deterministic analytics code first; the LLM only narrates.
- Keep dashboard, export, and AI tied to the same snapshot basis.
- Prefer narrow changes in the existing module boundaries.
- Do not add versioned `v2`, `v3`, or similar implementation names.
- Keep file edits small and targeted.
- Use the repo docs `CONTEXT.md` and `DESIGN.md` when the task touches terminology or UI.

When unsure, inspect the repo first and report concrete file paths, not guesses.
