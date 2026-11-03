from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_SECRET_KEY precisam estar configurados no backend.")
    return create_client(settings.supabase_url, settings.supabase_secret_key)


@lru_cache
def get_supabase_public() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY precisam estar configurados.")
    return create_client(settings.supabase_url, settings.supabase_publishable_key)
