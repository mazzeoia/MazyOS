from __future__ import annotations

from pydantic import BaseModel


class ProductEventRequest(BaseModel):
    evento: str
    metadata: dict = {}


class EventsSummaryResponse(BaseModel):
    since_days: int
    total: int
    by_event: dict[str, int]
