# Project Bootstrap Module Tasks

## Goal

Initialize the project so implementation work can start on stable ground:
environment setup, app skeletons, shared config, local scripts, and baseline
test/lint tooling for both frontend and backend.

## Tasks

- [x] Define the initial repo folder structure for `apps/`, `packages/`, `infra/`, and `doc/tasks/` alignment.
- [x] Initialize the frontend application skeleton with Next.js and TypeScript.
- [x] Initialize the backend application skeleton with FastAPI and Python project configuration.
- [x] Create shared environment variable strategy for frontend and backend.
- [x] Add example environment files for local development.
- [x] Add local development startup commands or scripts for frontend and backend.
- [x] Add local development documentation for install, run, and test commands.
- [x] Create shared code-quality configuration for formatting, linting, and type validation.
- [x] Create frontend test runner setup and base test directory structure.
- [x] Create backend test runner setup and base test directory structure.
- [x] Add baseline integration-test structure for frontend and backend.
- [x] Add placeholder directories for API routes, services, repositories, readers, mappers, aggregators, anomaly rules, insights, exports, and refresh jobs.
- [x] Add base dependency-injection or application wiring entrypoints for the backend.
- [x] Add base API health or smoke endpoint for startup verification.
- [x] Add fixture/seed bootstrap strategy for local development and automated tests.
- [x] Add initial CI workflow skeleton for install, lint, typecheck, and test jobs.
- [x] Verify the generated structure matches the modular boundaries defined in `ARCHITECTURE.md` and `doc/v1/detailed-design.md`.

## Testing

- [x] Verify frontend app boots locally.
- [x] Verify backend app boots locally.
- [x] Verify frontend unit test runner executes one sample test.
- [x] Verify backend unit test runner executes one sample test.
- [x] Verify lint and typecheck commands run successfully from a clean checkout.
- [x] Verify CI bootstrap pipeline can run on the initialized project structure.

## Exit Criteria

- [x] A new developer can clone the repo, install dependencies, start frontend and backend, and run baseline tests using documented commands.
- [x] The repo contains the required modular skeleton so feature modules can be implemented without re-planning project structure.
