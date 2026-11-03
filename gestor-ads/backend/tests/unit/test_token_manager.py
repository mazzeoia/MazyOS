from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.meta.token_manager import TokenManager, TokenPair


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def tm(fernet_key) -> TokenManager:
    return TokenManager(
        fernet_key=fernet_key,
        meta_app_id="test-app-id",
        meta_app_secret="test-app-secret",
    )


def test_encrypt_decrypt_round_trip(tm):
    encrypted = tm.encrypt("my-token-123")
    assert encrypted != "my-token-123"
    assert tm.decrypt(encrypted) == "my-token-123"


def test_token_pair_fields():
    tp = TokenPair(access_token="tok", expires_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert tp.access_token == "tok"
    assert tp.expires_at.year == 2026


@pytest.mark.asyncio
async def test_exchange_code_calls_meta(tm):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "short-lived", "expires_in": 3600}

    mock_extend_response = MagicMock()
    mock_extend_response.status_code = 200
    mock_extend_response.json.return_value = {"access_token": "long-lived", "expires_in": 5184000}

    with patch("app.meta.token_manager.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get.side_effect = [mock_response, mock_extend_response]
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        pair = await tm.exchange_code("auth-code-xyz")
        assert pair.access_token == "long-lived"
        assert pair.expires_at is not None


@pytest.mark.asyncio
async def test_exchange_code_raises_on_error(tm):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": {"message": "Invalid code"}}

    with patch("app.meta.token_manager.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get.return_value = mock_response
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        from app.shared.exceptions import MetaAPIError

        with pytest.raises(MetaAPIError):
            await tm.exchange_code("bad-code")


@pytest.mark.asyncio
async def test_refresh_if_needed_skips_fresh_token(tm):
    supabase = MagicMock()
    far_future = datetime(2026, 12, 31, tzinfo=timezone.utc).isoformat()
    supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "access_token_encrypted": tm.encrypt("still-valid"),
        "token_expires_at": far_future,
    }
    token = await tm.refresh_if_needed("conn-id-123", supabase)
    assert token == "still-valid"
