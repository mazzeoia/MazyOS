# tests/unit/test_meta_oauth.py
from __future__ import annotations

import pytest

from app.auth.meta_oauth import generate_oauth_url, validate_state


def test_generate_and_validate_state_without_conversation(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.com/callback")
    url = generate_oauth_url("user-1")
    state = url.split("state=")[1].split("&")[0]
    user_id, conversation_id = validate_state(state)
    assert user_id == "user-1"
    assert conversation_id is None


def test_generate_and_validate_state_with_conversation(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.com/callback")
    url = generate_oauth_url("user-1", conversation_id="conv-1")
    state = url.split("state=")[1].split("&")[0]
    user_id, conversation_id = validate_state(state)
    assert user_id == "user-1"
    assert conversation_id == "conv-1"


def test_validate_state_invalid_raises():
    with pytest.raises(ValueError):
        validate_state("nao-existe")
