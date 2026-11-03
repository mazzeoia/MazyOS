from __future__ import annotations

from fastapi import APIRouter

from ..supabase_client import get_supabase_public


router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("")
def overview() -> dict[str, object]:
    client = get_supabase_public()

    tables = {
        "organizations": client.table("organizations").select("id", count="exact").limit(1).execute(),
        "clients": client.table("clients").select("id", count="exact").limit(1).execute(),
        "campaigns": client.table("campaigns").select("id", count="exact").limit(1).execute(),
        "metrics": client.table("campaign_daily_metrics").select("id", count="exact").limit(1).execute(),
        "recommendations": client.table("recommendations").select("id", count="exact").limit(1).execute(),
    }

    return {
        "ok": True,
        "counts": {name: result.count or 0 for name, result in tables.items()},
    }
