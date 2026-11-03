from __future__ import annotations


def test_settings_loads_defaults():
    from app.config import Settings

    settings = Settings(
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
