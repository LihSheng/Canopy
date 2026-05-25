# Master Implementation Prompt: SecretStore Encryption Boundary

You are implementing Issue 2, `SecretStore Encryption`, in the Canopy repo.

Primary source documents:

- `doc/issues/0002-secret-store-encryption.md`
- `doc/high-level-design.md`
- `doc/detailed-design.md`
- `doc/adr/0002-secret-store-encryption-boundary.md`
- `ARCHITECTURE.md`

## Goal

Implement password-at-rest encryption for external connection credentials.

Scope:

- encrypt only `config_json.password`
- decrypt only when the service needs to read or use the password
- keep all other `config_json` fields readable
- do not auto-migrate legacy plaintext rows

## Main Agent Responsibility

You are the lead agent. Own the full change from start to finish.

Your job:

- read the docs above first
- break the work into module-sized sub-tasks
- assign implementation and tests to sub-agents
- integrate the results
- verify the repo against the acceptance criteria
- report only when the work is complete and checked

Do not ask the human to fill in gaps that can be resolved from the repo.
If a gap remains after reading the docs and code, ask one concise question.

## Sub-Agent Responsibility

Use sub-agents for isolated chunks of work:

- one sub-agent for `connection/secret_store.py`
- one sub-agent for `connection/service.py` and any read/write boundary changes
- one sub-agent for backend tests

Each sub-agent must:

- make narrow changes only
- keep the existing architecture intact
- add or update tests for the behavior it changes
- report file paths and test commands used

## Execution Model

No human intervention during implementation.

Workflow:

1. Read the design docs and issue.
2. Inspect the live code path for connection create/read/test/discover.
3. Implement the service boundary so `password` is encrypted on write and decrypted on read.
4. Keep the repository layer crypto-free.
5. Update or add tests for the actual feature boundary, not only the crypto primitive.
6. Run the required checks.
7. Fix failures.
8. Repeat until the acceptance criteria are satisfied.

## Required Behaviors

- `SecretStore` exposes `encrypt(plaintext: str) -> str` and `decrypt(ciphertext: str) -> str`
- AES-GCM uses a fresh nonce per call
- key is read from `SECRET_KEY` when not injected
- connection writes do not persist plaintext passwords
- connection reads return usable decrypted passwords through the service boundary
- connection test/discovery/preview use decrypted credentials
- legacy plaintext rows are not silently migrated

## Quality Gates

Use the repo's actual backend gates:

- `pytest`
- `ruff check`
- `ruff format --check`
- `mypy .`

At minimum, run the focused backend tests for this slice and any affected adjacent tests.

Recommended test focus:

- `apps/backend/tests/unit/test_secret_store.py`
- connection service tests that cover encrypted save and decrypted read
- any integration tests that exercise the connection test/discovery/preview path

Do not claim success until the relevant tests pass.

## How To Read The Task Breakdown

Use the issue docs under `doc/issues/` as the work map.

For this slice, the relevant scope is:

- Issue 1 for domain fields if you need them
- Issue 2 for SecretStore encryption
- Issue 3 if you need to confirm the decryption path for connection test/discovery

Do not widen the feature beyond the approved password-only boundary.

## Completion Criteria

The work is complete only when all of the following are true:

- `config_json.password` is encrypted before save
- `config_json.password` is decrypted on read and before external DB use
- non-secret config values remain readable
- legacy plaintext rows are not auto-migrated
- tests cover the service boundary, not just the crypto primitive
- the backend quality gates pass

## Reporting Format

When you finish, report:

1. What changed
2. Which files changed
3. Which tests ran
4. Which acceptance criteria are satisfied
5. Any residual risks or follow-up items

Keep the report concise and concrete.
