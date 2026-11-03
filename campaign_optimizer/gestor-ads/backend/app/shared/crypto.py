from __future__ import annotations

import base64
import hashlib
import hmac
import json

from cryptography.fernet import Fernet


def encrypt_token(plaintext: str, fernet_key: str) -> str:
    """Encrypt a token string for storage. Returns base64-encoded ciphertext."""
    f = Fernet(fernet_key.encode())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(encrypted: str, fernet_key: str) -> str:
    """Decrypt a stored token. Raises on invalid key or corrupted data."""
    f = Fernet(fernet_key.encode())
    return f.decrypt(encrypted.encode()).decode()


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode())


def parse_meta_signed_request(signed_request: str, app_secret: str) -> dict:
    """Parse and verify a Meta `signed_request` (used in deauthorize/data-deletion
    webhooks). Raises ValueError if the signature is missing, malformed, or invalid.
    """
    try:
        encoded_sig, payload = signed_request.split(".", 1)
    except ValueError as exc:
        raise ValueError("signed_request malformado") from exc

    sig = _b64url_decode(encoded_sig)
    data = json.loads(_b64url_decode(payload))

    if str(data.get("algorithm", "")).upper() != "HMAC-SHA256":
        raise ValueError(f"Algoritmo não suportado: {data.get('algorithm')}")

    expected_sig = hmac.new(app_secret.encode(), payload.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Assinatura do signed_request inválida")

    return data
