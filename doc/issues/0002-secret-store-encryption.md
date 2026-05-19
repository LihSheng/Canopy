# Issue 2: SecretStore Encryption

## Parent

PRD: doc/prd/0001-connection-wizard-sync-modes.md

## What to build

Abstract SecretStore protocol with AES-256-GCM implementation using SECRET_KEY env var. Wired into ConnectionService so credentials in config_json are encrypted before write and decrypted on read.

## Acceptance Criteria

- [ ] SecretStore abstract protocol defines `encrypt(plaintext: str) -> str` and `decrypt(ciphertext: str) -> str`
- [ ] AES-256-GCM implementation reads key from environment variable SECRET_KEY
- [ ] Nonce/IV generated per encryption call
- [ ] Wrong key raises clear decryption error
- [ ] ConnectionService encrypts credentials before storing
- [ ] ConnectionService decrypts credentials on read
- [ ] Unit tests: encrypt/decrypt round-trip, different keys produce different ciphertext, wrong key fails

## Blocked by

None - can start immediately (independent of Slice 1)
