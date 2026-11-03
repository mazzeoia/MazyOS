from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from app.meta.rate_limiter import RateLimiter, RateLimitStatus
from app.shared.audit import audit_write
from app.shared.exceptions import MetaAPIError, MetaRateLimitError

logger = logging.getLogger(__name__)

_RATE_LIMIT_CODES = {4, 17, 32, 613}


class MetaAdsClient:
    """Client for Meta Marketing API v23.0 — read and write."""

    BASE = "https://graph.facebook.com/v23.0"

    def __init__(
        self,
        access_token: str,
        act_id: str,
        rate_limiter: RateLimiter,
        user_id: str = "",
        audit_fn=None,
    ):
        self.token = access_token
        self.act_id = act_id
        self.limiter = rate_limiter
        self._user_id = user_id
        self._audit_fn = audit_fn
        self._http = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self._http.aclose()

    # === INTERNAL ===

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Central request method with rate limiting and error handling."""
        status = self.limiter.check(self.act_id)
        if status == RateLimitStatus.BLOCKED:
            raise MetaRateLimitError(
                f"Rate limit atingido para {self.act_id}. Aguarde.",
                meta={
                    "retry_after_seconds": self.limiter.throttle_seconds,
                    "account": self.act_id,
                },
            )
        if status == RateLimitStatus.THROTTLE:
            await asyncio.sleep(self.limiter.throttle_seconds)

        url = f"{self.BASE}{path}"

        # Inject access_token
        if method.upper() == "GET":
            params = kwargs.get("params", {})
            params["access_token"] = self.token
            kwargs["params"] = params
        else:
            data = kwargs.get("data", {})
            if isinstance(data, dict):
                data["access_token"] = self.token
                kwargs["data"] = data

        response = await self._http.request(method, url, **kwargs)

        # Update rate limiter from header
        usage_header = response.headers.get("X-Business-Use-Case-Usage", "")
        if usage_header:
            self.limiter.update_from_header(self.act_id, usage_header)

        result = response.json()

        if "error" in result:
            error = result["error"]
            code = error.get("code", 0)
            subcode = error.get("error_subcode", 0)
            message = error.get("message", "Meta API error")

            if code in _RATE_LIMIT_CODES or subcode in _RATE_LIMIT_CODES:
                raise MetaRateLimitError(
                    message,
                    meta={
                        "retry_after_seconds": self.limiter.throttle_seconds,
                        "account": self.act_id,
                    },
                )
            raise MetaAPIError(message, meta={"code": code, "subcode": subcode})

        return result

    @staticmethod
    def _extract_metric(items: list[dict[str, Any]] | None, match_terms: tuple[str, ...]) -> float:
        """Extract metric value from Meta actions array.

        Migrated from campaign_optimizer/connectors/meta_ads.py — proven logic.
        Searches for action_types matching any of the match_terms.
        """
        if not items:
            return 0.0
        total = 0.0
        for item in items:
            action_type = str(item.get("action_type", "")).lower()
            if any(term in action_type for term in match_terms):
                try:
                    total += float(item.get("value", 0) or 0)
                except (TypeError, ValueError):
                    continue
        return total

    # === READ ===

    async def get_account_info(self) -> dict:
        """Returns account id, name, status, currency, timezone."""
        return await self._request(
            "GET",
            f"/{self.act_id}",
            params={"fields": "id,name,account_status,currency,timezone_name"},
        )

    async def list_campaigns(self, limit: int = 200) -> list[dict]:
        """List campaigns with automatic pagination (max 10 pages)."""
        all_campaigns: list[dict] = []
        params = {
            "fields": "id,name,objective,status,daily_budget,lifetime_budget,effective_status",
            "limit": str(limit),
        }
        path = f"/{self.act_id}/campaigns"
        next_path: str | None = path
        next_params: dict | None = params
        page = 0

        while next_path and page < 10:
            data = await self._request("GET", next_path, params=next_params or {})
            all_campaigns.extend(data.get("data", []))
            paging = data.get("paging", {})
            next_url = paging.get("next")
            if next_url:
                next_path = next_url.replace(self.BASE, "")
                next_params = None
            else:
                next_path = None
            page += 1

        return all_campaigns

    async def get_insights(
        self,
        object_id: str,
        date_preset: str = "last_7d",
        level: str = "campaign",
    ) -> list[dict]:
        """Fetch aggregated metrics for an account or object."""
        fields = ",".join(
            [
                "campaign_name",
                "adset_name",
                "ad_name",
                "impressions",
                "reach",
                "clicks",
                "ctr",
                "cpc",
                "cpm",
                "spend",
                "frequency",
                "actions",
                "cost_per_action_type",
                "date_start",
                "date_stop",
            ]
        )
        data = await self._request(
            "GET",
            f"/{object_id}/insights",
            params={
                "fields": fields,
                "date_preset": date_preset,
                "level": level,
                "limit": "200",
            },
        )
        return data.get("data", [])

    async def list_adsets(self, campaign_id: str) -> list[dict]:
        data = await self._request(
            "GET",
            f"/{campaign_id}/adsets",
            params={"fields": "id,name,status,daily_budget,targeting,optimization_goal"},
        )
        return data.get("data", [])

    async def list_ads(self, adset_id: str) -> list[dict]:
        data = await self._request(
            "GET",
            f"/{adset_id}/ads",
            params={"fields": "id,name,status,creative"},
        )
        return data.get("data", [])

    # === WRITE ===

    @audit_write(action="create_campaign", entity="campaign")
    async def create_campaign(
        self,
        name: str,
        objective: str,
        special_ad_categories: list[str] | None = None,
        daily_budget_cents: int | None = None,
        lifetime_budget_cents: int | None = None,
    ) -> dict:
        """Create campaign — ALWAYS with status=PAUSED."""
        payload: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": json.dumps(special_ad_categories or []),
        }
        if daily_budget_cents is not None:
            payload["daily_budget"] = str(daily_budget_cents)
        if lifetime_budget_cents is not None:
            payload["lifetime_budget"] = str(lifetime_budget_cents)

        return await self._request("POST", f"/{self.act_id}/campaigns", data=payload)

    @audit_write(action="create_adset", entity="adset")
    async def create_adset(self, campaign_id: str, payload: dict) -> dict:
        data = {
            "campaign_id": campaign_id,
            "status": "PAUSED",
            **payload,
        }
        return await self._request("POST", f"/{self.act_id}/adsets", data=data)

    @audit_write(action="create_ad", entity="ad")
    async def create_ad(self, adset_id: str, creative_id: str, payload: dict) -> dict:
        data = {
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": "PAUSED",
            **payload,
        }
        return await self._request("POST", f"/{self.act_id}/ads", data=data)

    @audit_write(action="upload_image", entity="creative")
    async def upload_image(self, file_bytes: bytes, filename: str) -> dict:
        return await self._request(
            "POST",
            f"/{self.act_id}/adimages",
            data={"access_token": self.token},
            files={"filename": (filename, file_bytes)},
        )

    @audit_write(action="update_status", entity="campaign")
    async def update_status(self, entity_id: str, status: str) -> dict:
        """Change entity status (ACTIVE, PAUSED)."""
        return await self._request("POST", f"/{entity_id}", data={"status": status})
