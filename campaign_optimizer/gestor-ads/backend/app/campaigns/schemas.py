from __future__ import annotations

from pydantic import BaseModel


class AccountOut(BaseModel):
    id: str
    external_id: str
    name: str
    currency: str
    timezone: str
    status: str


class CampaignOut(BaseModel):
    id: str
    meta_campaign_id: str | None
    name: str
    objective: str | None
    status: str
    daily_budget: float | None
    lifetime_budget: float | None


class SyncRequest(BaseModel):
    act_id: str
    date_preset: str = "last_7d"


class SyncResponse(BaseModel):
    campaigns_synced: int
    metrics_upserted: int
    errors: list[dict]


class DraftCreate(BaseModel):
    act_id: str
    payload: dict


class DraftUpdate(BaseModel):
    payload: dict


class DraftOut(BaseModel):
    id: str
    status: str
    payload: dict
    meta_campaign_id: str | None
    erro_detalhes: str | None
