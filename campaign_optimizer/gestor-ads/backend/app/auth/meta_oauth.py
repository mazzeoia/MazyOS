from __future__ import annotations

import secrets
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.config import get_settings

# In-memory store for OAuth state tokens (state_key -> {user_id, expires_at})
# For single-instance deployment; use Redis for multi-instance.
_state_store: dict[str, dict] = {}
_state_lock = threading.Lock()


def _cleanup_expired() -> None:
    """Remove expired state entries."""
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _state_store.items() if v["expires_at"] < now]
    for k in expired:
        _state_store.pop(k, None)


def generate_oauth_url(user_id: str, conversation_id: str | None = None) -> str:
    """Generate Meta OAuth URL with opaque state token.

    conversation_id is set when the flow was started from the chat agent
    (Telegram/Evolution), so the callback knows which chat to notify.
    """
    settings = get_settings()

    # Generate a short opaque token (no dots, safe for Facebook redirect)
    state_key = secrets.token_urlsafe(32)

    # Store the mapping server-side
    with _state_lock:
        _cleanup_expired()
        _state_store[state_key] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        }

    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": "ads_management,ads_read,business_management,pages_show_list",
        "state": state_key,
        "response_type": "code",
    }
    return f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"


def validate_state(state: str) -> tuple[str, str | None]:
    """Validate opaque state token and return (user_id, conversation_id).
    Raises on invalid/expired."""
    with _state_lock:
        entry = _state_store.pop(state, None)

    if not entry:
        raise ValueError("State inválido ou expirado")

    if entry["expires_at"] < datetime.now(timezone.utc):
        raise ValueError("State expirado")

    return entry["user_id"], entry.get("conversation_id")
