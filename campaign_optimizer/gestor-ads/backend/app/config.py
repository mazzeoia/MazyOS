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
    anthropic_workspace_id: str = ""

    # Agent — Telegram
    telegram_bot_token: str = ""
    # Shared secret Telegram echoes back in X-Telegram-Bot-Api-Secret-Token
    # (registered via setWebhook's secret_token param). MUST be set in production.
    telegram_webhook_secret: str = ""

    # Web dashboard URL — chat users are told to log in here. The chat never
    # provisions accounts; linking happens through the Meta OAuth callback.
    frontend_url: str = "http://localhost:3000"

    # Agent — Evolution API (WhatsApp via QR, experimental channel)
    evolution_base_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = ""

    # Agent — Whisper (audio transcription)
    openai_api_key: str = ""

    # Email (SMTP) — used for automation notifications. Left blank, sending
    # is skipped silently (logged) until configured.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Creative Ads"

    # Automation — shared secret for the cron-triggered /automation/run-all
    # endpoint (no user JWT available from a server-side scheduler).
    automation_cron_secret: str = ""

    # App
    environment: str = "development"
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
