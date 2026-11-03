from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.shared.crypto import decrypt_token, encrypt_token


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


def test_encrypt_returns_string(fernet_key):
    result = encrypt_token("my-secret-token", fernet_key)
    assert isinstance(result, str)
    assert result != "my-secret-token"


def test_decrypt_round_trip(fernet_key):
    encrypted = encrypt_token("meta-access-token-abc123", fernet_key)
    decrypted = decrypt_token(encrypted, fernet_key)
    assert decrypted == "meta-access-token-abc123"


def test_decrypt_with_wrong_key(fernet_key):
    encrypted = encrypt_token("secret", fernet_key)
    wrong_key = Fernet.generate_key().decode()
    with pytest.raises(Exception):
        decrypt_token(encrypted, wrong_key)


def test_encrypt_empty_string(fernet_key):
    encrypted = encrypt_token("", fernet_key)
    assert decrypt_token(encrypted, fernet_key) == ""


def test_encrypt_unicode(fernet_key):
    token = "tøken-with-üñîcödé"
    encrypted = encrypt_token(token, fernet_key)
    assert decrypt_token(encrypted, fernet_key) == token
