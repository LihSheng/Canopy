# Issue 2: SecretStore Encryption

## Parent

PRD: [doc/prd/0001-connection-wizard-sync-modes.md](C:/Users/Lih%20Sheng/Documents/Canopy/doc/prd/0001-connection-wizard-sync-modes.md)

## Scope

Provide a `SecretStore` abstraction with an AES-256-GCM implementation keyed by `SECRET_KEY`.
Wire it into `ConnectionService` so `config_json.password` is encrypted before storage and
decrypted on read.

This issue only covers the `password` field. Other `config_json` fields remain readable.

## Out of Scope

- Encrypting the entire `config_json` blob
- Automatic backfill or migration of legacy plaintext credentials
- Other secret fields that may be added in future tickets
- AWS Secrets Manager integration

## Acceptance Criteria

- [ ] `SecretStore` defines `encrypt(plaintext: str) -> str` and `decrypt(ciphertext: str) -> str`
- [ ] AES-256-GCM implementation reads its key from `SECRET_KEY`
- [ ] A fresh nonce/IV is generated on every encryption call
- [ ] Wrong key raises a clear decryption error
- [ ] `ConnectionService` encrypts `config_json.password` before storing
- [ ] `ConnectionService` decrypts `config_json.password` on read
- [ ] Existing plaintext credentials are not silently changed by this issue
- [ ] Unit tests cover round-trip encryption, different keys producing different ciphertext, and wrong-key failure

## Test Notes

- Verify round-trip encryption and decryption with a known plaintext
- Verify ciphertext differs when the key differs
- Verify a wrong key fails with a clear error
- Verify `ConnectionService` only encrypts/decrypts the password field
- Verify existing plaintext rows are not auto-migrated by this ticket

## Blocked By

None. This slice can start independently.
