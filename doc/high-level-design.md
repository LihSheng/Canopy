# High-Level Design: SecretStore Encryption Boundary

## Overview

This slice adds an at-rest encryption boundary for external connection credentials.
The system must keep `config_json.password` encrypted while leaving the rest of
`config_json` readable so connection setup, test, discovery, and debugging can
still inspect non-secret metadata.

The approved boundary is narrow:

- encrypt only `config_json.password`
- decrypt only when a service needs the password value
- do not encrypt the full `config_json` blob
- do not auto-migrate legacy plaintext rows in this issue

## Design Principles

- Keep the crypto primitive isolated behind a `SecretStore` abstraction.
- Keep encryption and decryption at the service boundary, not in the repository.
- Keep non-secret connection metadata readable.
- Keep the feature backward-compatible for new writes while leaving legacy data
  migration for a separate follow-up.
- Fail clearly when the key is missing, wrong, or the ciphertext is invalid.

## Major Modules

### 1. SecretStore Module

Responsibilities:

- define a small encrypt/decrypt interface for secret strings
- provide an AES-256-GCM implementation
- read its key from `SECRET_KEY`
- produce portable ciphertext strings

### 2. Connection Service Boundary Module

Responsibilities:

- encrypt `config_json.password` before a connection is stored
- decrypt `config_json.password` when a connection is read
- decrypt credentials before connection test, discovery, and preview calls
- keep the rest of `config_json` unchanged

### 3. Connection Persistence Module

Responsibilities:

- persist the connection record and its `config_json`
- store encrypted password strings as opaque values
- merge config metadata without introducing crypto concerns

### 4. External Connection Access Module

Responsibilities:

- use the decrypted password when validating or connecting to external sources
- keep source-adapter code unaware of storage encryption details

### 5. Error Handling Module

Responsibilities:

- surface clear errors for missing `SECRET_KEY`
- surface clear errors for tampered ciphertext or wrong keys
- avoid silent fallback to plaintext when decryption fails

## Data Flow

1. User creates or updates a connection with a password.
2. Connection service encrypts `config_json.password`.
3. Repository persists the encrypted value.
4. Later, a read or external DB operation loads the connection.
5. Connection service decrypts `config_json.password` before use.
6. The rest of `config_json` remains readable and unchanged.

## Interfaces

### Backend Interfaces

- `SecretStore.encrypt(plaintext: str) -> str`
- `SecretStore.decrypt(ciphertext: str) -> str`
- `ConnectionService.create_connection(...)`
- `ConnectionService.get_connection(...)`
- `ConnectionService.test_connection(...)`
- `ConnectionService.discover_tables(...)`
- `ConnectionService.preview_table(...)`

### Persistence Interfaces

- `connections.config_json.password` stores encrypted ciphertext
- other `config_json` fields remain plaintext

## Cross-Cutting Concerns

### Security

- Passwords must not be written to storage in plaintext for new writes.
- Decryption must be deterministic and fail loudly when the key is wrong.
- The encryption key must come from deployment configuration.

### Compatibility

- Existing plaintext rows are not automatically migrated in this issue.
- Only new or updated connection writes are in scope.

### Observability

- Crypto failures should be distinguishable from connection-test failures.
- Errors should make it obvious whether the problem is config, keying, or source
  connectivity.

## Main Tradeoffs

### Encrypt Only Password, Not Full Config

Chosen approach:

- encrypt the secret field only

Tradeoff:

- less general than full-blob encryption
- much easier to debug and safer for operational metadata

### Service-Layer Boundary, Not Repository-Layer Crypto

Chosen approach:

- keep encryption and decryption in `ConnectionService`

Tradeoff:

- more explicit code paths
- repository stays simpler and reusable

### No Automatic Legacy Backfill

Chosen approach:

- leave old plaintext rows alone in this issue

Tradeoff:

- safer and less risky for this slice
- requires a separate migration ticket if historical data must be fixed

## Deferred Items

- encrypting additional secret fields in `config_json`
- automatic legacy data backfill
- AWS Secrets Manager integration
- key rotation tooling and re-encryption migration

