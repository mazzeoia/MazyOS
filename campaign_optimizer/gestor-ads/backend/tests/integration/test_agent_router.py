# tests/integration/test_agent_router.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.agent.main import app
from app.dependencies import get_supabase

# Hermetic: never build a real Supabase client from env vars in this test —
# the endpoints only need `Depends(get_supabase)` to resolve to *something*
# so the request can be dispatched to the background task.
app.dependency_overrides[get_supabase] = lambda: MagicMock()


def test_telegram_webhook_acks_immediately():
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        client = TestClient(app)
        payload = {"message": {"chat": {"id": 555}, "text": "oi"}}
        response = client.post("/agent/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_evolution_webhook_acks_immediately():
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        client = TestClient(app)
        payload = {"data": {"key": {"remoteJid": "5585999@s.whatsapp.net"}, "message": {"conversation": "oi"}}}
        response = client.post("/agent/evolution/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


# --- webhook shared-secret auth (C3) ---

import pytest

from app.config import Settings, get_settings

_SECRET_SETTINGS = Settings(telegram_webhook_secret="s3cr3t", evolution_api_key="evo-key")


@pytest.fixture
def secret_client():
    app.dependency_overrides[get_settings] = lambda: _SECRET_SETTINGS
    yield TestClient(app)
    app.dependency_overrides.pop(get_settings, None)


TELEGRAM_PAYLOAD = {"message": {"chat": {"id": 555}, "text": "oi"}}
EVOLUTION_PAYLOAD = {"data": {"key": {"remoteJid": "5585999@s.whatsapp.net"}, "message": {"conversation": "oi"}}}


def test_telegram_webhook_accepts_valid_secret(secret_client):
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        resp = secret_client.post(
            "/agent/telegram/webhook",
            json=TELEGRAM_PAYLOAD,
            headers={"X-Telegram-Bot-Api-Secret-Token": "s3cr3t"},
        )
    assert resp.status_code == 200


def test_telegram_webhook_rejects_wrong_secret(secret_client):
    process = AsyncMock()
    with patch("app.agent.router.process_incoming_message", new=process):
        resp = secret_client.post(
            "/agent/telegram/webhook",
            json=TELEGRAM_PAYLOAD,
            headers={"X-Telegram-Bot-Api-Secret-Token": "errado"},
        )
    assert resp.status_code == 401
    process.assert_not_called()


def test_telegram_webhook_rejects_missing_secret(secret_client):
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        resp = secret_client.post("/agent/telegram/webhook", json=TELEGRAM_PAYLOAD)
    assert resp.status_code == 401


def test_evolution_webhook_accepts_valid_apikey(secret_client):
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        resp = secret_client.post(
            "/agent/evolution/webhook", json=EVOLUTION_PAYLOAD, headers={"apikey": "evo-key"}
        )
    assert resp.status_code == 200


def test_evolution_webhook_rejects_wrong_apikey(secret_client):
    process = AsyncMock()
    with patch("app.agent.router.process_incoming_message", new=process):
        resp = secret_client.post(
            "/agent/evolution/webhook", json=EVOLUTION_PAYLOAD, headers={"apikey": "errado"}
        )
    assert resp.status_code == 401
    process.assert_not_called()


def test_evolution_webhook_rejects_missing_apikey(secret_client):
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        resp = secret_client.post("/agent/evolution/webhook", json=EVOLUTION_PAYLOAD)
    assert resp.status_code == 401
