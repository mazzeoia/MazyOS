from __future__ import annotations

from cryptography.fernet import Fernet


def encrypt_token(plaintext: str, fernet_key: str) -> str:
    """Encrypt a token string for storage. Returns base64-encoded ciphertext."""
    f = Fernet(fernet_key.encode())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(encrypted: str, fernet_key: str) -> str:
    """Decrypt a stored token. Raises on invalid key or corrupted data."""
    f = Fernet(fernet_key.encode())
    return f.decrypt(encrypted.encode()).decode()
