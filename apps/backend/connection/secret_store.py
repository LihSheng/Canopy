"""SecretStore encryption interface and AES-256-GCM implementation.

Usage:
    store = AesGcmSecretStore()
    ciphertext = store.encrypt("sensitive data")
    plaintext = store.decrypt(ciphertext)
    assert plaintext == "sensitive data"
"""

import os
from abc import ABC, abstractmethod
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError

ENCRYPTED_VALUE_PREFIX = "enc:v1:"


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class SecretStore(ABC):
    """Encrypts and decrypts sensitive credentials at rest."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext and return a portable string."""

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext back to the original plaintext."""


def is_encrypted_value(value: object) -> bool:
    """Return True when a value uses the versioned encrypted payload format."""
    return isinstance(value, str) and value.startswith(ENCRYPTED_VALUE_PREFIX)


def decrypt_secret_value(
    value: object,
    store: SecretStore,
    *,
    allow_legacy_plaintext: bool = False,
) -> object:
    """Decrypt a secret value or optionally pass through legacy plaintext.

    Legacy plaintext is only allowed when the caller explicitly opts in.
    """
    if not isinstance(value, str) or not value:
        return value
    if not value.startswith(ENCRYPTED_VALUE_PREFIX):
        if allow_legacy_plaintext:
            return value
        raise EncryptionError(f"Encrypted value must start with {ENCRYPTED_VALUE_PREFIX}")
    return store.decrypt(value)


class AesGcmSecretStore(SecretStore):
    """AES-256-GCM encryption backed by an application key.

    The ciphertext format is: ``enc:v1:`` + base64(nonce || ciphertext || tag)
    where || denotes concatenation.

    Parameters
    ----------
    key : bytes, optional
        A 32-byte AES-256 key. If None, reads from the SECRET_KEY
        environment variable.
    """

    _KEY_ENV_VAR = "SECRET_KEY"

    def __init__(self, key: bytes | None = None):
        if key is None:
            raw = os.environ.get(self._KEY_ENV_VAR)
            if raw is None:
                raise EncryptionError(f"{self._KEY_ENV_VAR} environment variable is not set")
            key = raw.encode("utf-8")
        if len(key) not in (16, 24, 32):
            raise EncryptionError(f"Key must be 16, 24, or 32 bytes long; got {len(key)}")
        self._key = key

    def encrypt(self, plaintext: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return ENCRYPTED_VALUE_PREFIX + b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not ciphertext.startswith(ENCRYPTED_VALUE_PREFIX):
            raise EncryptionError(f"Ciphertext must start with {ENCRYPTED_VALUE_PREFIX}")

        encoded = ciphertext.removeprefix(ENCRYPTED_VALUE_PREFIX)
        try:
            raw = b64decode(encoded)
        except (BinasciiError, ValueError) as exc:
            raise EncryptionError(f"Invalid ciphertext encoding: {exc}") from exc
        nonce = raw[:12]
        ct_and_tag = raw[12:]
        if not ct_and_tag:
            raise EncryptionError("Ciphertext too short")
        aesgcm = AESGCM(self._key)
        try:
            plaintext = aesgcm.decrypt(nonce, ct_and_tag, None)
        except Exception as exc:
            raise EncryptionError(f"Decryption failed: {exc}") from exc
        return plaintext.decode("utf-8")
