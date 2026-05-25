# Task

{{TASK}}

# Issue context

!`if [ -n "{{ISSUE_NUMBER}}" ]; then gh issue view {{ISSUE_NUMBER}} --json title,body,comments --jq '"Title: \(.title)\n\n\(.body)"' || echo "Issue #{{ISSUE_NUMBER}} not found. Follow the task above directly."; else echo "No issue specified. Follow the task above directly."; fi`

# Instructions

You are an AI coding agent working on this repository.

## Before editing

1. Read `ARCHITECTURE.md`, `CONTEXT.md`, and `DESIGN.md` to understand the project.
2. Explore the relevant parts of the codebase.
3. Understand the existing patterns before making changes.

## During editing

1. Make the smallest safe change to accomplish the task.
2. Follow existing code style and module boundaries.
3. Keep business logic in services or domain modules, not route handlers or UI components.
4. Keep changes narrow and preserve existing module boundaries.
5. Do not invent metrics; compute them in code first.
6. Keep dashboard, export, and AI aligned to the same snapshot.
7. Prefer readable code over clever batching.
8. Do not refactor unrelated code.

## After editing

1. Run any available static checks (typecheck, lint) if practical.
2. Run relevant tests.
3. Fix any issues found.

## Commit

1. Create a single commit with all changes.
2. Commit message must include:
   - A clear summary of what changed.
   - List of files modified.
3. Do not leave uncommitted changes.

## Completion

When the task is complete, output `<promise>COMPLETE</promise>` on its own line.
