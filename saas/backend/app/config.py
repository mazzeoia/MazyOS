from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / ".env").exists()),
    Path(__file__).resolve().parents[1],
)
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    app_name: str = "Creative Campaign OS"
    environment: str = "local"
    app_url: str = "http://127.0.0.1:3000"
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_api_version: str = "v21.0"
    meta_webhook_verify_token: str = ""
    meta_oauth_scopes: str = (
        "ads_read,ads_management,business_management,pages_show_list,pages_read_engagement"
    )
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_developer_token: str = ""
    google_ads_login_customer_id: str = ""
    google_ads_api_version: str = "v25"
    google_ads_oauth_scopes: str = "https://www.googleapis.com/auth/adwords"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://ads.creativeagenciamkt.com.br"

    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def meta_scope_list(self) -> list[str]:
        return [scope.strip() for scope in self.meta_oauth_scopes.split(",") if scope.strip()]

    @property
    def google_ads_scope_list(self) -> list[str]:
        return [scope.strip() for scope in self.google_ads_oauth_scopes.split(",") if scope.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
