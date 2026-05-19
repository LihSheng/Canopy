# 0002 - SecretStore Encryption Boundary for Connection Credentials

Third-party database credentials (host, port, username, password, database name)
entered during the Connection Wizard are stored encrypted at rest using AES-256-GCM
behind a `SecretStore` interface. The runtime implementation uses an application-level
encryption key from an environment variable; the interface is designed for a future
swap to AWS Secrets Manager without schema or service-layer changes.

## Status

Accepted.

## Considered Options

1. **Plain-text storage** — simplest but unacceptable for production. A database dump
   or debug log would expose external database credentials.

2. **Hashed comparison only / no storage** — credentials validated once and discarded.
   The backend assumes a persistent sidecar proxy or VPN tunnel handles reconnection.
   Too restrictive for the deployment patterns this platform targets.

3. **Encrypted storage with SecretStore interface (chosen)** — credentials encrypted
   with AES-256-GCM before write, decrypted at pull time, key from `SECRET_KEY`
   environment variable. The encryption logic is behind a `SecretStore` protocol/ABC
   so swapping to AWS Secrets Manager is a new implementation of the same interface.

## Consequences

- The `Connection.config_json` field stores encrypted password values. The
  `SecretStore` is responsible for encrypt/decrypt at the storage boundary.
- The encryption key must be set in the deployment environment. A missing or
  mismatched key causes connection test and pull failures with a clear error.
- Rotating the key requires re-encrypting all stored credentials. This is a
  documented operational procedure, not an automated runtime behavior.
- AWS Secrets Manager migration path: implement the `SecretStore` interface
  with `boto3`, swap the dependency injection binding, run a one-time migration
  script to move existing encrypted values to AWS, and delete the local key.
  No domain model, schema, or API contract changes required.
