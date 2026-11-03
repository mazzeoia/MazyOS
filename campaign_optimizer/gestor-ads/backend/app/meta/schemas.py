from __future__ import annotations

from pydantic import BaseModel


class CampaignCreatePayload(BaseModel):
    name: str
    objective: str
    special_ad_categories: list[str] = []
    daily_budget_cents: int | None = None
    lifetime_budget_cents: int | None = None


class AdSetPayload(BaseModel):
    name: str
    daily_budget_cents: int | None = None
    targeting: dict = {}
    optimization_goal: str = "LEAD_GENERATION"
    billing_event: str = "IMPRESSIONS"
    start_time: str | None = None
    end_time: str | None = None


class AdPayload(BaseModel):
    name: str
    status: str = "PAUSED"
