from __future__ import annotations

import json
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.meta.client import MetaAdsClient
from app.meta.rate_limiter import RateLimiter
from app.shared.exceptions import MetaAPIError, MetaRateLimitError


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


@pytest.fixture
def client(limiter) -> MetaAdsClient:
    return MetaAdsClient(
        access_token="test-token",
        act_id="act_123",
        rate_limiter=limiter,
        user_id="user-1",
        audit_fn=AsyncMock(),
    )


# --- _extract_metric (migrated from campaign_optimizer) ---


def test_extract_metric_finds_leads():
    actions = [
        {"action_type": "link_click", "value": "50"},
        {"action_type": "messaging_conversation_started", "value": "7"},
        {"action_type": "lead", "value": "3"},
    ]
    result = MetaAdsClient._extract_metric(actions, ("messaging_conversation_started", "lead", "contact", "omni_lead"))
    assert result == 10.0


def test_extract_metric_returns_zero_for_none():
    assert MetaAdsClient._extract_metric(None, ("lead",)) == 0.0


def test_extract_metric_returns_zero_for_empty():
    assert MetaAdsClient._extract_metric([], ("lead",)) == 0.0


def test_extract_metric_handles_bad_value():
    actions = [{"action_type": "lead", "value": "not-a-number"}]
    assert MetaAdsClient._extract_metric(actions, ("lead",)) == 0.0


# --- _request ---


@pytest.mark.asyncio
@respx.mock
async def test_request_success(client):
    route = respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            200,
            json={"id": "act_123", "name": "Test Account"},
            headers={
                "X-Business-Use-Case-Usage": json.dumps(
                    {
                        "act_123": [
                            {
                                "call_count": 5,
                                "total_cputime": 5,
                                "total_time": 5,
                                "type": "ads_management",
                                "estimated_time_to_regain_access": 0,
                            }
                        ]
                    }
                )
            },
        )
    )
    result = await client._request("GET", "/act_123")
    assert result == {"id": "act_123", "name": "Test Account"}
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_request_meta_error(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            400,
            json={
                "error": {
                    "message": "Invalid token",
                    "code": 190,
                    "error_subcode": 463,
                }
            },
        )
    )
    with pytest.raises(MetaAPIError, match="Invalid token"):
        await client._request("GET", "/act_123")


@pytest.mark.asyncio
@respx.mock
async def test_request_rate_limit_error(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            400,
            json={
                "error": {
                    "message": "limit reached",
                    "code": 4,
                    "error_subcode": 17,
                }
            },
        )
    )
    with pytest.raises(MetaRateLimitError):
        await client._request("GET", "/act_123")


# --- Read methods ---


@pytest.mark.asyncio
@respx.mock
async def test_get_account_info(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "act_123",
                "name": "Conta",
                "account_status": 1,
                "currency": "BRL",
                "timezone_name": "America/Sao_Paulo",
            },
        )
    )
    info = await client.get_account_info()
    assert info["name"] == "Conta"
    assert info["currency"] == "BRL"


@pytest.mark.asyncio
@respx.mock
async def test_list_campaigns(client):
    respx.get("https://graph.facebook.com/v23.0/act_123/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"id": "c1", "name": "Camp 1"},
                    {"id": "c2", "name": "Camp 2"},
                ],
                "paging": {},
            },
        )
    )
    camps = await client.list_campaigns()
    assert len(camps) == 2
    assert camps[0]["name"] == "Camp 1"


@pytest.mark.asyncio
@respx.mock
async def test_get_insights(client):
    respx.get("https://graph.facebook.com/v23.0/act_123/insights").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "impressions": "1000",
                        "clicks": "50",
                        "spend": "100.00",
                        "ctr": "5.0",
                        "cpc": "2.0",
                        "cpm": "100.0",
                        "frequency": "1.5",
                        "reach": "800",
                        "actions": [{"action_type": "lead", "value": "5"}],
                        "cost_per_action_type": [{"action_type": "lead", "value": "20.0"}],
                    }
                ],
                "paging": {},
            },
        )
    )
    data = await client.get_insights("act_123")
    assert len(data) == 1
    assert data[0]["spend"] == "100.00"


# --- Write methods ---


@pytest.mark.asyncio
@respx.mock
async def test_create_campaign_forces_paused(client):
    respx.post("https://graph.facebook.com/v23.0/act_123/campaigns").mock(
        return_value=httpx.Response(200, json={"id": "999"})
    )
    result = await client.create_campaign(
        name="[TEST] | leads | sp | 20260827-1400",
        objective="OUTCOME_LEADS",
        special_ad_categories=[],
        daily_budget_cents=5000,
    )
    assert result == {"id": "999"}
    sent = respx.calls[0].request
    assert b"PAUSED" in sent.content


@pytest.mark.asyncio
@respx.mock
async def test_update_status(client):
    respx.post("https://graph.facebook.com/v23.0/campaign_555").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await client.update_status("campaign_555", "ACTIVE")
    assert result["success"] is True


@pytest.mark.asyncio
@respx.mock
async def test_upload_image(client):
    respx.post("https://graph.facebook.com/v23.0/act_123/adimages").mock(
        return_value=httpx.Response(200, json={"images": {"image.jpg": {"hash": "abc123"}}})
    )
    result = await client.upload_image(b"fake-image-bytes", "image.jpg")
    assert "images" in result
