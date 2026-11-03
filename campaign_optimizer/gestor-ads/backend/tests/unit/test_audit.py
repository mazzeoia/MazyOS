from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.shared.audit import audit_write


class FakeClient:
    """Simulates MetaAdsClient with _audit_fn and _user_id."""

    def __init__(self, audit_fn=None):
        self._audit_fn = audit_fn
        self._user_id = "user-abc"

    @audit_write(action="create_campaign", entity="campaign")
    async def create_something(self, payload: dict) -> dict:
        return {"id": "123", "status": "PAUSED"}

    @audit_write(action="update_status", entity="campaign")
    async def failing_method(self, payload: dict) -> dict:
        raise ValueError("Meta API exploded")


@pytest.mark.asyncio
async def test_audit_calls_fn_on_success():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    result = await client.create_something({"name": "test"})
    assert result == {"id": "123", "status": "PAUSED"}
    audit_fn.assert_called_once()
    call_kwargs = audit_fn.call_args.kwargs
    assert call_kwargs["action"] == "create_campaign"
    assert call_kwargs["entity"] == "campaign"
    assert call_kwargs["response"] == {"id": "123", "status": "PAUSED"}
    assert call_kwargs["error"] is None


@pytest.mark.asyncio
async def test_audit_calls_fn_on_error():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    with pytest.raises(ValueError, match="exploded"):
        await client.failing_method({"entity_id": "456"})
    audit_fn.assert_called_once()
    call_kwargs = audit_fn.call_args.kwargs
    assert call_kwargs["action"] == "update_status"
    assert call_kwargs["error"] is not None
    assert "exploded" in call_kwargs["error"]


@pytest.mark.asyncio
async def test_audit_skips_if_no_fn():
    client = FakeClient(audit_fn=None)
    result = await client.create_something({"name": "test"})
    assert result == {"id": "123", "status": "PAUSED"}


@pytest.mark.asyncio
async def test_audit_captures_user_id():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    await client.create_something({"name": "x"})
    assert audit_fn.call_args.kwargs["user_id"] == "user-abc"
