"""Token encryption utilities for stored OAuth credentials."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr


class TokenEncryptionError(Exception):
    """Raised when token encryption or decryption fails."""


def derive_fernet_key(secret: SecretStr) -> bytes:
    """Derive a Fernet-compatible key from an application secret."""
    raw = secret.get_secret_value().encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


class TokenEncryptor:
    """Encrypt and decrypt sensitive token material at rest."""

    def __init__(self, secret: SecretStr) -> None:
        self._fernet = Fernet(derive_fernet_key(secret))

    def encrypt(self, value: str) -> str:
        """Return an encrypted token string."""
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a stored token string."""
        try:
            return self._fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise TokenEncryptionError("Stored token could not be decrypted") from exc
