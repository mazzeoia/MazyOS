from __future__ import annotations


def test_settings_loads_defaults():
    from app.config import Settings

    # Disable .env loading so a local `ENVIRONMENT=production` in the repo's
    # .env file can't leak into this test's expectations.
    settings = Settings(
        _env_file=None,
        fernet_key="test-key",
        jwt_secret="test-secret",
    )
    assert settings.environment == "development"
    assert settings.log_level == "info"
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.supabase_url == ""
    assert settings.meta_app_id == ""
    assert settings.anthropic_api_key == ""


def test_settings_from_env(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("META_APP_ID", "999")
    monkeypatch.setenv("FERNET_KEY", "abc")
    monkeypatch.setenv("JWT_SECRET", "xyz")
    settings = Settings()
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.meta_app_id == "999"


def test_get_settings_returns_instance():
    import os

    os.environ.setdefault("FERNET_KEY", "k")
    os.environ.setdefault("JWT_SECRET", "s")
    from app.config import get_settings

    s = get_settings()
    assert hasattr(s, "supabase_url")


def test_settings_have_agent_fields(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tg-token")
    monkeypatch.setenv("EVOLUTION_BASE_URL", "http://evolution-go:8080")
    monkeypatch.setenv("EVOLUTION_API_KEY", "evo-key")
    monkeypatch.setenv("EVOLUTION_INSTANCE", "creative-ads")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = Settings()
    assert settings.telegram_bot_token == "tg-token"
    assert settings.evolution_base_url == "http://evolution-go:8080"
    assert settings.evolution_api_key == "evo-key"
    assert settings.evolution_instance == "creative-ads"
    assert settings.openai_api_key == "sk-test"
