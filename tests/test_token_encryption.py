"""Tests for token encryption utilities."""

import pytest
from pydantic import SecretStr

from musicbloom.security.token_encryption import TokenEncryptionError, TokenEncryptor


def test_encrypt_and_decrypt_round_trip() -> None:
    encryptor = TokenEncryptor(SecretStr("development-token-encryption-key"))

    encrypted = encryptor.encrypt("spotify-access-token")
    decrypted = encryptor.decrypt(encrypted)

    assert encrypted != "spotify-access-token"
    assert decrypted == "spotify-access-token"


def test_decrypt_invalid_payload_raises() -> None:
    encryptor = TokenEncryptor(SecretStr("development-token-encryption-key"))

    with pytest.raises(TokenEncryptionError):
        encryptor.decrypt("not-a-valid-token")
