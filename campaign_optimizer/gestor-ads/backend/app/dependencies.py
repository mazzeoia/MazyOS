from __future__ import annotations

from fastapi import Depends, Header
from supabase import Client, create_client

from app.auth.models import User
from app.config import Settings, get_settings
from app.meta.client import MetaAdsClient
from app.meta.rate_limiter import RateLimiter
from app.meta.token_manager import TokenManager
from app.shared.exceptions import TokenInvalidError

# Module-level singletons
_rate_limiter = RateLimiter()


def get_supabase(settings: Settings = Depends(get_settings)) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


async def get_current_user(
    authorization: str = Header(...),
    settings: Settings = Depends(get_settings),
) -> User:
    """Validate Supabase JWT and return user."""
    token = authorization.replace("Bearer ", "")
    if not token:
        raise TokenInvalidError()

    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        result = supabase.auth.get_user(token)
        if not result or not result.user:
            raise TokenInvalidError()
        return User(id=str(result.user.id), email=result.user.email or "")
    except Exception as exc:
        if isinstance(exc, TokenInvalidError):
            raise
        raise TokenInvalidError() from exc


def get_token_manager(settings: Settings = Depends(get_settings)) -> TokenManager:
    return TokenManager(
        fernet_key=settings.fernet_key,
        meta_app_id=settings.meta_app_id,
        meta_app_secret=settings.meta_app_secret,
    )


async def build_meta_client(
    act_id: str,
    user: User,
    supabase: Client,
    settings: Settings,
) -> MetaAdsClient:
    """Build a MetaAdsClient — callable from DI or directly from router code.

    Schema adaptation: ad_accounts uses client_id (not user_id) and
    external_id (not act_id). meta_connections uses owner_id.
    """
    tm = TokenManager(
        fernet_key=settings.fernet_key,
        meta_app_id=settings.meta_app_id,
        meta_app_secret=settings.meta_app_secret,
    )

    # Find the meta connection for this user
    connection = supabase.table("meta_connections").select("id").eq("owner_id", user.id).single().execute().data

    token = await tm.refresh_if_needed(connection["id"], supabase)

    async def audit_fn(*, user_id, action, entity, request, response, error):
        supabase.table("audit_log").insert(
            {
                "owner_id": user_id,
                "acao": action,
                "entidade": entity,
                "request": request if isinstance(request, dict) else {"raw": str(request)},
                "response": response if isinstance(response, dict) else {"raw": str(response)},
                "origem": "api",
            }
        ).execute()

    return MetaAdsClient(
        access_token=token,
        act_id=act_id,
        rate_limiter=_rate_limiter,
        user_id=user.id,
        audit_fn=audit_fn,
    )


async def get_meta_client(
    act_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
) -> MetaAdsClient:
    """FastAPI DI wrapper around build_meta_client."""
    return await build_meta_client(act_id, user, supabase, settings)
