from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, object]:
    settings = get_settings()
    return {
        "ok": True,
        "app": settings.app_name,
        "environment": settings.environment,
        "supabase_configured": bool(settings.supabase_url and settings.supabase_publishable_key),
        "admin_key_configured": bool(settings.supabase_secret_key),
    }
