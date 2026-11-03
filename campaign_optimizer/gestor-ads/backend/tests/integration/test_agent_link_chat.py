# tests/integration/test_agent_link_chat.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.auth.models import User
from app.dependencies import get_current_user, get_supabase
from app.main import app

FAKE_USER = User(id="user-1", email="dono@example.com")


def _client(supabase: MagicMock) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    app.dependency_overrides[get_supabase] = lambda: supabase
    return TestClient(app)


def _reset():
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_supabase, None)


def test_link_chat_requires_auth():
    supabase = MagicMock()
    app.dependency_overrides[get_supabase] = lambda: supabase
    try:
        client = TestClient(app)
        resp = client.post("/agent/link-chat", json={"code": "123456"})
        # Missing Authorization header: FastAPI's required Header(...) dependency
        # (get_current_user) rejects with 422 before the route body runs — the
        # same behavior every other JWT-protected route in this backend has.
        assert resp.status_code == 422
    finally:
        _reset()


def test_link_chat_success_links_conversation_and_notifies():
    supabase = MagicMock()
    conv_chain = supabase.table.return_value.select.return_value.eq.return_value.gt.return_value
    conv_chain.execute.return_value.data = [
        {"id": "conv-1", "channel": "telegram", "channel_user_id": "555", "owner_id": None}
    ]
    # No existing meta connection -> tells the user to connect Meta next.
    supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.agent.dashboard_router._adapter_for") as mock_adapter_for:
        adapter = MagicMock()
        adapter.send_text = AsyncMock()
        mock_adapter_for.return_value = adapter

        client = _client(supabase)
        try:
            resp = client.post("/agent/link-chat", json={"code": "482913"})
        finally:
            _reset()

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["conversation_id"] == "conv-1"
    assert body["channel"] == "telegram"
    adapter.send_text.assert_awaited_once()

    args, kwargs = supabase.table.return_value.update.call_args
    assert args[0]["owner_id"] == "user-1"
    assert args[0]["link_code"] is None


def test_link_chat_invalid_code_returns_404():
    supabase = MagicMock()
    conv_chain = supabase.table.return_value.select.return_value.eq.return_value.gt.return_value
    conv_chain.execute.return_value.data = []

    client = _client(supabase)
    try:
        resp = client.post("/agent/link-chat", json={"code": "000000"})
    finally:
        _reset()

    assert resp.status_code == 404


def test_link_chat_already_used_code_returns_404():
    """A code cleared after a previous successful link must not link again."""
    supabase = MagicMock()
    conv_chain = supabase.table.return_value.select.return_value.eq.return_value.gt.return_value
    conv_chain.execute.return_value.data = []

    client = _client(supabase)
    try:
        resp = client.post("/agent/link-chat", json={"code": "482913"})
    finally:
        _reset()

    assert resp.status_code == 404
