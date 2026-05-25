# Detailed Design: SecretStore Encryption Boundary

## Scope Alignment

This design implements the `SecretStore` boundary for connection passwords only.
It follows the accepted rule from `doc/issues/0002-secret-store-encryption.md`
and the boundary decision in `doc/adr/0002-secret-store-encryption-boundary.md`.

The implementation must:

- keep `config_json.password` encrypted at rest
- decrypt the password when the connection is read or used for external access
- leave non-secret `config_json` fields readable
- avoid migrating legacy plaintext rows automatically

## Module Design

### 1. SecretStore Module

#### Responsibilities

- define a minimal secret-string interface
- encrypt plaintext with AES-256-GCM
- decrypt ciphertext back to plaintext
- read the application key from `SECRET_KEY`

#### Data Structures

- `SecretStore`
  - `encrypt(plaintext: str) -> str`
  - `decrypt(ciphertext: str) -> str`
- `EncryptionError`
  - raised when crypto setup or decryption fails

#### Ciphertext Format

- base64-encoded `nonce || ciphertext || tag`
- use a fresh 12-byte nonce on every encryption call
- keep the encoded value safe to store in JSON

#### Key Handling

- read `SECRET_KEY` from the environment when no key is injected
- require a valid AES-256 key length for the production path
- reject missing or malformed keys with a clear error

#### Error Handling

- missing key raises `EncryptionError`
- wrong key raises `EncryptionError`
- tampered ciphertext raises `EncryptionError`
- invalid base64 payload raises `EncryptionError`

#### Tests

- round-trip encrypt/decrypt
- different keys produce different ciphertext
- wrong key fails
- tampered ciphertext fails
- missing `SECRET_KEY` fails

### 2. Connection Service Boundary Module

#### Responsibilities

- encrypt connection passwords before persistence
- decrypt connection passwords on read
- decrypt passwords before external connection operations
- keep non-secret config values unchanged

#### Data Structures

- `Connection.config_json`
  - dictionary payload stored on the connection record
  - `password` is encrypted when present
  - all other keys remain readable

#### Control Flow

##### Create connection

1. Receive the incoming `config_json`.
2. If `password` is present and non-empty, encrypt it.
3. Save the connection with the encrypted password.
4. Return the saved domain object with the decrypted password only if the caller
   needs a read shape.

##### Read connection

1. Load the connection record from the repository.
2. Copy `config_json` into a service-local dict.
3. If `password` is present, decrypt it.
4. Return the domain object or read shape with the plaintext password only for
   service use.

##### External DB operations

1. Read the connection.
2. Decrypt `config_json.password`.
3. Call the adapter with the decrypted credential payload.

#### Public Interfaces

- `ConnectionService.create_connection(...)`
- `ConnectionService.get_connection(id)`
- `ConnectionService.test_connection(id)`
- `ConnectionService.discover_tables(id)`
- `ConnectionService.preview_table(id, table)`

#### Error Handling

- if `password` is absent, decryption is skipped
- if decryption fails, the service surfaces a clear error instead of silently
  falling back to plaintext
- if the connection does not exist, preserve existing not-found behavior

#### Tests

- create stores encrypted password
- read returns decrypted password through the service boundary
- test/discover/preview decrypt before adapter calls
- absent password is a no-op

### 3. Repository Module

#### Responsibilities

- persist connection data without crypto concerns
- merge config metadata safely
- read and write the model fields unchanged

#### Rule

- the repository must not know whether `config_json.password` is encrypted or
  plaintext
- repository methods should accept the already-prepared config payload from the
  service layer

#### Tests

- saving and loading connection config preserves keys and values
- non-secret config metadata survives update merges

### 4. External Connection Access Module

#### Responsibilities

- use decrypted credentials for connection test, discovery, and preview
- keep adapter code focused on source connectivity and metadata discovery

#### Control Flow

- service decrypts password
- adapter receives plain credentials
- adapter performs source-level operations

#### Tests

- service passes decrypted password to adapter
- adapter-facing code does not attempt to decrypt on its own

### 5. Error Handling And Validation Module

#### Responsibilities

- distinguish crypto failures from source connectivity failures
- keep failure messages actionable for operators

#### Error Classes

- `EncryptionError`
- existing validation or not-found errors

#### Failure Cases

- missing `SECRET_KEY`
- wrong `SECRET_KEY`
- tampered ciphertext
- invalid ciphertext format

## Persistence Strategy

- store encrypted password inside `connections.config_json.password`
- keep host, port, database, username, and other metadata plaintext
- do not mutate legacy plaintext rows automatically
- leave any backfill script or migration for a separate issue

## Configuration Strategy

- production and local dev must provide `SECRET_KEY`
- tests may inject a key directly or monkeypatch the environment
- the implementation should fail fast if the key is missing

## Error Handling Strategy

- crypto setup errors should be explicit and immediate
- decryption failures should be explicit and not masked as adapter failures
- connection lookup failures keep the existing not-found response shape

## Test Strategy

### Unit Tests

- SecretStore round-trip
- wrong-key failure
- tampered ciphertext failure
- missing-key failure
- deterministic ciphertext uniqueness per encryption call

### Service Tests

- encrypted save path
- decrypted read path
- test/discover/preview use decrypted credentials
- non-secret config remains readable

### Integration Tests

- connection API creates and reads encrypted credentials
- connection test endpoint uses decrypted credentials successfully

## Known Risks

- legacy plaintext rows may exist and will remain unencrypted in this issue
- accidental double-encryption can break reads if a service boundary is missed
- key rotation is out of scope and should not be implied by this slice
- too-broad encryption would make operational debugging harder, so the password-
  only boundary should stay explicit
