from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.auth.meta_oauth import generate_oauth_url, validate_state


def test_generate_oauth_url_has_required_params():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="test-secret-key-for-testing",
        )
        url = generate_oauth_url("user-uuid-123")
        assert "client_id=12345" in url
        assert "redirect_uri=" in url
        assert "ads_management" in url
        assert "state=" in url


def test_validate_state_round_trip():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="test-secret-key-for-testing",
        )
        url = generate_oauth_url("user-uuid-123")
        state = url.split("state=")[1].split("&")[0]
        user_id, conversation_id = validate_state(state)
        assert user_id == "user-uuid-123"
        assert conversation_id is None


def test_validate_state_rejects_unknown_state():
    # State is now an opaque token in a server-side store (not a signed JWT),
    # so a value that was never issued by generate_oauth_url must be rejected.
    with pytest.raises(ValueError):
        validate_state("some-token-nobody-issued")


def test_validate_state_rejects_reuse():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="test-secret-key-for-testing",
        )
        url = generate_oauth_url("user-uuid-123")
        state = url.split("state=")[1].split("&")[0]

        assert validate_state(state) == ("user-uuid-123", None)
        with pytest.raises(ValueError):
            validate_state(state)
