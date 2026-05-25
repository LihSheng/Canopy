"""Tests for SecretStore encryption."""

from base64 import b64decode, b64encode

import pytest

from connection.secret_store import (
    ENCRYPTED_VALUE_PREFIX,
    AesGcmSecretStore,
    EncryptionError,
    decrypt_secret_value,
)

# 32 bytes for AES-256
_TEST_KEY = bytes(range(32))


class TestAesGcmSecretStore:
    """Round-trip encryption/decryption with the same key should return the original text."""

    def test_encrypt_then_decrypt_returns_original(self):
        store = AesGcmSecretStore(key=_TEST_KEY)
        plaintext = "hello world"
        ciphertext = store.encrypt(plaintext)
        assert ciphertext.startswith(ENCRYPTED_VALUE_PREFIX)
        decrypted = store.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_different_keys_produce_different_ciphertexts(self):
        store_a = AesGcmSecretStore(key=bytes(range(32)))
        store_b = AesGcmSecretStore(key=bytes(range(32, 64)))
        plaintext = "secret"
        ct_a = store_a.encrypt(plaintext)
        ct_b = store_b.encrypt(plaintext)
        assert ct_a != ct_b

    def test_wrong_key_raises_encryption_error(self):
        store = AesGcmSecretStore(key=bytes(range(32)))
        wrong_store = AesGcmSecretStore(key=bytes(range(32, 64)))
        ciphertext = store.encrypt("hello")
        with pytest.raises(EncryptionError, match="Decryption failed"):
            wrong_store.decrypt(ciphertext)

    def test_tampered_ciphertext_raises_encryption_error(self):
        store = AesGcmSecretStore(key=_TEST_KEY)
        ciphertext = store.encrypt("hello")
        # Decode base64, flip a byte in the binary, re-encode
        raw = bytearray(b64decode(ciphertext.removeprefix(ENCRYPTED_VALUE_PREFIX)))
        raw[len(raw) // 2] ^= 1
        tampered = ENCRYPTED_VALUE_PREFIX + b64encode(bytes(raw)).decode("ascii")
        with pytest.raises(EncryptionError, match="Decryption failed"):
            store.decrypt(tampered)

    def test_missing_env_var_raises_encryption_error(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.delenv(AesGcmSecretStore._KEY_ENV_VAR, raising=False)
            with pytest.raises(EncryptionError, match="SECRET_KEY"):
                AesGcmSecretStore()

    def test_each_encrypt_call_produces_unique_ciphertext(self):
        store = AesGcmSecretStore(key=_TEST_KEY)
        results = {store.encrypt("same data") for _ in range(10)}
        assert len(results) == 10

    def test_legacy_plaintext_helper_can_pass_through(self):
        store = AesGcmSecretStore(key=_TEST_KEY)
        assert decrypt_secret_value("legacy-plain", store, allow_legacy_plaintext=True) == "legacy-plain"

    def test_plaintext_rejected_without_legacy_flag(self):
        store = AesGcmSecretStore(key=_TEST_KEY)
        with pytest.raises(EncryptionError, match="enc:v1:"):
            decrypt_secret_value("legacy-plain", store, allow_legacy_plaintext=False)
