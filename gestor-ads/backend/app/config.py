from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""

    # Meta OAuth
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = ""

    # Security
    fernet_key: str = ""
    jwt_secret: str = ""

    # LLM
    anthropic_api_key: str = ""

    # App
    environment: str = "development"
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
