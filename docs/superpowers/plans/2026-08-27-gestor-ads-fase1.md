# Gestor Ads — Fase 1: Backend Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend that connects to Meta Ads (read+write), runs a rules engine, analyzes campaigns with Claude AI, and exposes REST endpoints — serving as the shared foundation for the web dashboard (Phase 2) and WhatsApp agent (Phase 3).

**Architecture:** Modular monolith — a single FastAPI application with internal modules (`auth/`, `meta/`, `core/`, `shared/`). Multi-tenant via Supabase RLS from day 1. Meta tokens encrypted with Fernet. All write operations audited. Campaigns always created as PAUSED.

**Tech Stack:** Python 3.12, FastAPI, httpx (async), Supabase (PostgreSQL + Auth + RLS + Storage), Anthropic SDK (Claude Sonnet 5), cryptography (Fernet), pydantic-settings, pytest + respx, ruff, Docker

**Spec:** `docs/superpowers/specs/2026-08-27-gestor-ads-fase1-design.md`

## Global Constraints

- Python ≥ 3.12
- FastAPI ≥ 0.115, pydantic ≥ 2.10, pydantic-settings ≥ 2.7
- httpx ≥ 0.28 (async only — no `requests`)
- Meta Graph API v23.0
- All Meta tokens encrypted with Fernet at rest — never stored plaintext
- Campaigns always created with `status=PAUSED`
- Advantage+ / automatic targeting disabled by default
- Naming convention: `[MARCA] | objetivo | publico | AAAAMMDD-HHMM`
- `nivel_tecnico` (`leigo` | `avancado`) changes language only, never strategy
- RLS policy on every table: `user_id = auth.uid()`
- Portuguese BR for user-facing strings, English for code identifiers
- Project root: `gestor-ads/backend/` (relative to repo root)

---

## File Structure

```
gestor-ads/
└── backend/
    ├── pyproject.toml
    ├── Dockerfile
    ├── .env.example
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                  # FastAPI app, CORS, exception handler, router mounts
    │   ├── config.py                # pydantic-settings, all env vars
    │   ├── dependencies.py          # get_current_user, get_supabase, get_meta_client
    │   ├── shared/
    │   │   ├── __init__.py
    │   │   ├── exceptions.py        # AppError hierarchy (6 classes)
    │   │   ├── crypto.py            # encrypt_token / decrypt_token (Fernet)
    │   │   └── audit.py             # @audit_write decorator
    │   ├── meta/
    │   │   ├── __init__.py
    │   │   ├── client.py            # MetaAdsClient — read + write + _request + _extract_metric
    │   │   ├── schemas.py           # Pydantic models for campaigns, insights, payloads
    │   │   ├── token_manager.py     # TokenManager — encrypt, decrypt, exchange, extend, revoke
    │   │   └── rate_limiter.py      # RateLimiter — parse header, check usage
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── rules.py             # RuleResult, AccountThresholds, evaluate()
    │   │   ├── kpis.py              # KPISummary, summarize_kpis()
    │   │   ├── naming.py            # campaign_name, adset_name, ad_name
    │   │   └── analysis.py          # analyze_performance, fallback_analysis, generate_campaign_strategy
    │   ├── auth/
    │   │   ├── __init__.py
    │   │   ├── router.py            # /register, /login, /meta/login, /meta/callback
    │   │   ├── meta_oauth.py        # generate_oauth_url, validate_state, handle_callback
    │   │   └── models.py            # RegisterRequest, LoginRequest, AuthResponse, etc.
    │   ├── campaigns/
    │   │   ├── __init__.py
    │   │   ├── router.py            # /accounts, /campaigns, /sync, /drafts, /activate, /pause
    │   │   └── schemas.py           # CampaignOut, DraftCreate, SyncResponse, etc.
    │   └── analysis/
    │       ├── __init__.py
    │       ├── router.py            # /evaluate, /summary, /creatives, /audit-log
    │       └── schemas.py           # EvaluateResponse, SummaryResponse, etc.
    ├── migrations/
    │   └── 001_initial_schema.sql   # All 8 tables + RLS + trigger
    └── tests/
        ├── __init__.py
        ├── conftest.py              # Shared fixtures
        ├── unit/
        │   ├── __init__.py
        │   ├── test_config.py
        │   ├── test_exceptions.py
        │   ├── test_crypto.py
        │   ├── test_token_manager.py
        │   ├── test_rate_limiter.py
        │   ├── test_audit.py
        │   ├── test_meta_client.py
        │   ├── test_rules.py
        │   ├── test_kpis.py
        │   ├── test_naming.py
        │   └── test_analysis.py
        └── integration/
            ├── __init__.py
            ├── test_auth_flow.py
            ├── test_sync_flow.py
            └── test_campaign_routers.py
```

---

### Task 1: Project Scaffolding + Config + Exceptions

**Files:**
- Create: `gestor-ads/backend/pyproject.toml`
- Create: `gestor-ads/backend/app/__init__.py`
- Create: `gestor-ads/backend/app/config.py`
- Create: `gestor-ads/backend/app/shared/__init__.py`
- Create: `gestor-ads/backend/app/shared/exceptions.py`
- Create: `gestor-ads/backend/tests/__init__.py`
- Create: `gestor-ads/backend/tests/unit/__init__.py`
- Create: `gestor-ads/backend/tests/conftest.py`
- Test: `gestor-ads/backend/tests/unit/test_config.py`
- Test: `gestor-ads/backend/tests/unit/test_exceptions.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces:
  - `Settings` class with fields: `supabase_url`, `supabase_service_key`, `supabase_anon_key`, `meta_app_id`, `meta_app_secret`, `meta_redirect_uri`, `fernet_key`, `jwt_secret`, `anthropic_api_key`, `environment`, `log_level`, `cors_origins`
  - `get_settings() -> Settings`
  - Exception classes: `AppError`, `MetaAPIError`, `MetaRateLimitError`, `TokenExpiredError`, `TokenInvalidError`, `DraftValidationError`, `CampaignSafetyError`

- [ ] **Step 1: Create project structure and pyproject.toml**

Create all directories and the `pyproject.toml`:

```toml
# gestor-ads/backend/pyproject.toml
[project]
name = "gestor-ads"
version = "0.1.0"
description = "Backend unificado — Campaign Optimizer + Gestor de Tráfego"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "httpx>=0.28",
    "supabase>=2.12",
    "anthropic>=0.45",
    "cryptography>=44.0",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "python-jose[cryptography]>=3.3",
    "python-multipart>=0.0.18",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "respx>=0.22",
    "ruff>=0.8",
]

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Create empty `__init__.py` files:
- `gestor-ads/backend/app/__init__.py`
- `gestor-ads/backend/app/shared/__init__.py`
- `gestor-ads/backend/tests/__init__.py`
- `gestor-ads/backend/tests/unit/__init__.py`

- [ ] **Step 2: Write the failing tests for config**

```python
# gestor-ads/backend/tests/unit/test_config.py
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
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd gestor-ads/backend
pip install -e ".[dev]"
pytest tests/unit/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 4: Implement config.py**

```python
# gestor-ads/backend/app/config.py
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
```

- [ ] **Step 5: Run config tests — verify they pass**

```bash
pytest tests/unit/test_config.py -v
```

Expected: 3 passed

- [ ] **Step 6: Write the failing tests for exceptions**

```python
# gestor-ads/backend/tests/unit/test_exceptions.py
from __future__ import annotations

from app.shared.exceptions import (
    AppError,
    CampaignSafetyError,
    DraftValidationError,
    MetaAPIError,
    MetaRateLimitError,
    TokenExpiredError,
    TokenInvalidError,
)


def test_app_error_defaults():
    err = AppError()
    assert err.status_code == 500
    assert err.error_code == "INTERNAL_ERROR"
    assert err.detail == "Erro interno"
    assert err.meta == {}


def test_app_error_custom_detail():
    err = AppError("algo quebrou", meta={"key": "val"})
    assert err.detail == "algo quebrou"
    assert err.meta == {"key": "val"}
    assert str(err) == "algo quebrou"


def test_meta_api_error_is_502():
    err = MetaAPIError("falha na Meta")
    assert err.status_code == 502
    assert err.error_code == "META_API_ERROR"
    assert isinstance(err, AppError)


def test_meta_rate_limit_is_429():
    err = MetaRateLimitError("limite atingido")
    assert err.status_code == 429
    assert err.error_code == "META_RATE_LIMIT"
    assert isinstance(err, MetaAPIError)
    assert isinstance(err, AppError)


def test_token_expired_message():
    err = TokenExpiredError()
    assert err.status_code == 401
    assert "Reconecte" in err.detail


def test_token_invalid_message():
    err = TokenInvalidError()
    assert err.status_code == 401
    assert err.error_code == "TOKEN_INVALID"


def test_draft_validation_is_422():
    err = DraftValidationError("campo faltando")
    assert err.status_code == 422
    assert err.error_code == "DRAFT_INVALID"


def test_campaign_safety_is_403():
    err = CampaignSafetyError()
    assert err.status_code == 403
    assert "segurança" in err.detail.lower()


def test_exception_hierarchy():
    """MetaRateLimitError → MetaAPIError → AppError → Exception."""
    err = MetaRateLimitError("test")
    assert isinstance(err, MetaAPIError)
    assert isinstance(err, AppError)
    assert isinstance(err, Exception)
```

- [ ] **Step 7: Run exception tests — verify they fail**

```bash
pytest tests/unit/test_exceptions.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.shared.exceptions'`

- [ ] **Step 8: Implement exceptions.py**

```python
# gestor-ads/backend/app/shared/exceptions.py
from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str = "Erro interno", *, meta: dict | None = None):
        self.detail = detail
        self.meta = meta or {}
        super().__init__(detail)


class MetaAPIError(AppError):
    status_code = 502
    error_code = "META_API_ERROR"


class MetaRateLimitError(MetaAPIError):
    status_code = 429
    error_code = "META_RATE_LIMIT"


class TokenExpiredError(AppError):
    status_code = 401
    error_code = "TOKEN_EXPIRED"

    def __init__(self):
        super().__init__("Token Meta expirado. Reconecte sua conta.")


class TokenInvalidError(AppError):
    status_code = 401
    error_code = "TOKEN_INVALID"

    def __init__(self):
        super().__init__("Token inválido ou ausente.")


class DraftValidationError(AppError):
    status_code = 422
    error_code = "DRAFT_INVALID"


class CampaignSafetyError(AppError):
    status_code = 403
    error_code = "SAFETY_BLOCK"

    def __init__(self):
        super().__init__("Ação bloqueada por regra de segurança.")
```

- [ ] **Step 9: Run all tests — verify they pass**

```bash
pytest tests/unit/test_config.py tests/unit/test_exceptions.py -v
```

Expected: all tests pass

- [ ] **Step 10: Create conftest.py with shared fixtures**

```python
# gestor-ads/backend/tests/conftest.py
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Prevent real env vars from leaking into tests."""
    monkeypatch.setenv("FERNET_KEY", "VGVzdEtleUZvclRlc3Rpbmc9PT09PT09PT09PT09PQ==")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-unit-tests")
    monkeypatch.setenv("ENVIRONMENT", "test")


@pytest.fixture
def fake_supabase():
    """Mock Supabase client for unit tests."""
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    client.table.return_value.insert.return_value.execute.return_value.data = [{}]
    client.table.return_value.upsert.return_value.execute.return_value.data = [{}]
    return client


@pytest.fixture
def fake_audit_fn():
    """Mock audit function for MetaAdsClient tests."""
    return AsyncMock()
```

- [ ] **Step 11: Run ruff check**

```bash
ruff check app/ tests/
ruff format --check app/ tests/
```

Expected: no errors

- [ ] **Step 12: Commit**

```bash
git add gestor-ads/
git commit -m "feat(gestor-ads): scaffold project, config, and exception hierarchy

- pyproject.toml with all Phase 1 dependencies
- Settings via pydantic-settings (all env vars)
- AppError hierarchy: MetaAPIError, MetaRateLimitError, TokenExpiredError,
  TokenInvalidError, DraftValidationError, CampaignSafetyError
- conftest.py with env isolation and mock fixtures
- 12 tests passing"
```

---

### Task 2: Crypto Module + Token Manager

**Files:**
- Create: `gestor-ads/backend/app/shared/crypto.py`
- Create: `gestor-ads/backend/app/meta/__init__.py`
- Create: `gestor-ads/backend/app/meta/token_manager.py`
- Test: `gestor-ads/backend/tests/unit/test_crypto.py`
- Test: `gestor-ads/backend/tests/unit/test_token_manager.py`

**Interfaces:**
- Consumes: `Settings.fernet_key` from Task 1
- Produces:
  - `encrypt_token(plaintext: str, fernet_key: str) -> str`
  - `decrypt_token(encrypted: str, fernet_key: str) -> str`
  - `TokenManager` class with methods: `encrypt(token) -> str`, `decrypt(encrypted) -> str`, `exchange_code(code) -> TokenPair`, `extend_token(short_lived) -> TokenPair`, `refresh_if_needed(connection_id, supabase) -> str`, `revoke(connection_id, supabase) -> None`
  - `TokenPair` dataclass: `access_token: str`, `expires_at: datetime`

- [ ] **Step 1: Write the failing tests for crypto**

```python
# gestor-ads/backend/tests/unit/test_crypto.py
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.shared.crypto import decrypt_token, encrypt_token


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


def test_encrypt_returns_string(fernet_key):
    result = encrypt_token("my-secret-token", fernet_key)
    assert isinstance(result, str)
    assert result != "my-secret-token"


def test_decrypt_round_trip(fernet_key):
    encrypted = encrypt_token("meta-access-token-abc123", fernet_key)
    decrypted = decrypt_token(encrypted, fernet_key)
    assert decrypted == "meta-access-token-abc123"


def test_decrypt_with_wrong_key(fernet_key):
    encrypted = encrypt_token("secret", fernet_key)
    wrong_key = Fernet.generate_key().decode()
    with pytest.raises(Exception):
        decrypt_token(encrypted, wrong_key)


def test_encrypt_empty_string(fernet_key):
    encrypted = encrypt_token("", fernet_key)
    assert decrypt_token(encrypted, fernet_key) == ""


def test_encrypt_unicode(fernet_key):
    token = "tøken-with-üñîcödé"
    encrypted = encrypt_token(token, fernet_key)
    assert decrypt_token(encrypted, fernet_key) == token
```

- [ ] **Step 2: Run crypto tests — verify they fail**

```bash
cd gestor-ads/backend
pytest tests/unit/test_crypto.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement crypto.py**

```python
# gestor-ads/backend/app/shared/crypto.py
from __future__ import annotations

from cryptography.fernet import Fernet


def encrypt_token(plaintext: str, fernet_key: str) -> str:
    """Encrypt a token string for storage. Returns base64-encoded ciphertext."""
    f = Fernet(fernet_key.encode())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(encrypted: str, fernet_key: str) -> str:
    """Decrypt a stored token. Raises on invalid key or corrupted data."""
    f = Fernet(fernet_key.encode())
    return f.decrypt(encrypted.encode()).decode()
```

- [ ] **Step 4: Run crypto tests — verify they pass**

```bash
pytest tests/unit/test_crypto.py -v
```

Expected: 5 passed

- [ ] **Step 5: Write the failing tests for TokenManager**

```python
# gestor-ads/backend/tests/unit/test_token_manager.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.meta.token_manager import TokenManager, TokenPair


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def tm(fernet_key) -> TokenManager:
    return TokenManager(
        fernet_key=fernet_key,
        meta_app_id="test-app-id",
        meta_app_secret="test-app-secret",
    )


def test_encrypt_decrypt_round_trip(tm):
    encrypted = tm.encrypt("my-token-123")
    assert encrypted != "my-token-123"
    assert tm.decrypt(encrypted) == "my-token-123"


def test_token_pair_fields():
    tp = TokenPair(access_token="tok", expires_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert tp.access_token == "tok"
    assert tp.expires_at.year == 2026


@pytest.mark.asyncio
async def test_exchange_code_calls_meta(tm):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "short-lived", "expires_in": 3600}

    mock_extend_response = MagicMock()
    mock_extend_response.status_code = 200
    mock_extend_response.json.return_value = {"access_token": "long-lived", "expires_in": 5184000}

    with patch("app.meta.token_manager.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get.side_effect = [mock_response, mock_extend_response]
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        pair = await tm.exchange_code("auth-code-xyz")
        assert pair.access_token == "long-lived"
        assert pair.expires_at is not None


@pytest.mark.asyncio
async def test_exchange_code_raises_on_error(tm):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": {"message": "Invalid code"}}

    with patch("app.meta.token_manager.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get.return_value = mock_response
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance

        from app.shared.exceptions import MetaAPIError

        with pytest.raises(MetaAPIError):
            await tm.exchange_code("bad-code")


@pytest.mark.asyncio
async def test_refresh_if_needed_skips_fresh_token(tm):
    supabase = MagicMock()
    far_future = datetime(2026, 12, 31, tzinfo=timezone.utc).isoformat()
    supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "access_token_encrypted": tm.encrypt("still-valid"),
        "token_expires_at": far_future,
    }
    token = await tm.refresh_if_needed("conn-id-123", supabase)
    assert token == "still-valid"
```

- [ ] **Step 6: Run token manager tests — verify they fail**

```bash
pytest tests/unit/test_token_manager.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 7: Implement token_manager.py**

Create `gestor-ads/backend/app/meta/__init__.py` (empty).

```python
# gestor-ads/backend/app/meta/token_manager.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.shared.crypto import decrypt_token, encrypt_token
from app.shared.exceptions import MetaAPIError


@dataclass
class TokenPair:
    access_token: str
    expires_at: datetime


class TokenManager:
    """Manages Meta OAuth tokens — encrypt, decrypt, exchange, extend, refresh, revoke."""

    GRAPH_URL = "https://graph.facebook.com/v23.0"

    def __init__(self, fernet_key: str, meta_app_id: str, meta_app_secret: str):
        self._fernet_key = fernet_key
        self._app_id = meta_app_id
        self._app_secret = meta_app_secret

    def encrypt(self, token: str) -> str:
        return encrypt_token(token, self._fernet_key)

    def decrypt(self, encrypted: str) -> str:
        return decrypt_token(encrypted, self._fernet_key)

    async def exchange_code(self, code: str) -> TokenPair:
        """Exchange authorization code for a long-lived token.

        Flow: code → short-lived token → long-lived token (60 days).
        """
        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: code → short-lived
            resp = await client.get(
                f"{self.GRAPH_URL}/oauth/access_token",
                params={
                    "client_id": self._app_id,
                    "client_secret": self._app_secret,
                    "code": code,
                },
            )
            data = resp.json()
            if resp.status_code != 200 or "error" in data:
                msg = data.get("error", {}).get("message", "Erro ao trocar código OAuth")
                raise MetaAPIError(msg)

            short_lived = data["access_token"]

            # Step 2: short-lived → long-lived
            return await self.extend_token(short_lived, client)

    async def extend_token(
        self, short_lived: str, client: httpx.AsyncClient | None = None
    ) -> TokenPair:
        """Exchange a short-lived token for a long-lived one (60 days)."""
        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=30)

        try:
            resp = await client.get(
                f"{self.GRAPH_URL}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self._app_id,
                    "client_secret": self._app_secret,
                    "fb_exchange_token": short_lived,
                },
            )
            data = resp.json()
            if resp.status_code != 200 or "error" in data:
                msg = data.get("error", {}).get("message", "Erro ao estender token")
                raise MetaAPIError(msg)

            expires_in = int(data.get("expires_in", 5184000))
            return TokenPair(
                access_token=data["access_token"],
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        finally:
            if should_close:
                await client.aclose()

    async def refresh_if_needed(self, connection_id: str, supabase) -> str:
        """If token expires within 7 days, extend it. Returns decrypted token.

        If refresh fails, marks connection as is_valid=False.
        """
        row = (
            supabase.table("meta_connections")
            .select("access_token_encrypted, token_expires_at")
            .eq("id", connection_id)
            .single()
            .execute()
            .data
        )

        token = self.decrypt(row["access_token_encrypted"])
        expires_at = datetime.fromisoformat(row["token_expires_at"])

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        days_left = (expires_at - datetime.now(timezone.utc)).days

        if days_left > 7:
            return token

        try:
            pair = await self.extend_token(token)
            encrypted = self.encrypt(pair.access_token)
            supabase.table("meta_connections").update(
                {
                    "access_token_encrypted": encrypted,
                    "token_expires_at": pair.expires_at.isoformat(),
                    "atualizado_em": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", connection_id).execute()
            return pair.access_token
        except MetaAPIError:
            supabase.table("meta_connections").update(
                {"is_valid": False}
            ).eq("id", connection_id).execute()
            raise

    async def revoke(self, connection_id: str, supabase) -> None:
        """Revoke token on Meta and delete the connection."""
        row = (
            supabase.table("meta_connections")
            .select("access_token_encrypted")
            .eq("id", connection_id)
            .single()
            .execute()
            .data
        )
        token = self.decrypt(row["access_token_encrypted"])

        async with httpx.AsyncClient(timeout=30) as client:
            await client.delete(
                f"{self.GRAPH_URL}/me/permissions",
                params={"access_token": token},
            )

        supabase.table("meta_connections").delete().eq("id", connection_id).execute()
```

- [ ] **Step 8: Run all tests — verify they pass**

```bash
pytest tests/unit/test_crypto.py tests/unit/test_token_manager.py -v
```

Expected: all passed

- [ ] **Step 9: Commit**

```bash
git add gestor-ads/backend/app/shared/crypto.py gestor-ads/backend/app/meta/
git add gestor-ads/backend/tests/unit/test_crypto.py gestor-ads/backend/tests/unit/test_token_manager.py
git commit -m "feat(gestor-ads): Fernet crypto module and TokenManager

- encrypt_token / decrypt_token with round-trip
- TokenManager: exchange_code, extend_token, refresh_if_needed, revoke
- 10 tests passing"
```

---

### Task 3: Rate Limiter

**Files:**
- Create: `gestor-ads/backend/app/meta/rate_limiter.py`
- Test: `gestor-ads/backend/tests/unit/test_rate_limiter.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `RateLimitStatus` enum: `OK`, `THROTTLE`, `BLOCKED`
  - `RateLimiter` class with methods: `update_from_header(act_id: str, header_value: str) -> None`, `check(act_id: str) -> RateLimitStatus`, property `throttle_seconds -> int`

- [ ] **Step 1: Write the failing tests**

```python
# gestor-ads/backend/tests/unit/test_rate_limiter.py
from __future__ import annotations

import json

import pytest

from app.meta.rate_limiter import RateLimiter, RateLimitStatus


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


def test_unknown_account_returns_ok(limiter):
    assert limiter.check("act_unknown") == RateLimitStatus.OK


def test_low_usage_returns_ok(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 10,
                    "total_cputime": 5,
                    "total_time": 5,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 0,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.OK


def test_high_usage_returns_throttle(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 80,
                    "total_cputime": 80,
                    "total_time": 80,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 0,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.THROTTLE


def test_critical_usage_returns_blocked(limiter):
    header = json.dumps(
        {
            "act_123": [
                {
                    "call_count": 96,
                    "total_cputime": 96,
                    "total_time": 96,
                    "type": "ads_management",
                    "estimated_time_to_regain_access": 300,
                }
            ]
        }
    )
    limiter.update_from_header("act_123", header)
    assert limiter.check("act_123") == RateLimitStatus.BLOCKED


def test_throttle_seconds_default(limiter):
    assert limiter.throttle_seconds >= 30


def test_update_replaces_previous(limiter):
    low = json.dumps({"act_1": [{"call_count": 10, "total_cputime": 10, "total_time": 10, "type": "ads_management", "estimated_time_to_regain_access": 0}]})
    high = json.dumps({"act_1": [{"call_count": 96, "total_cputime": 96, "total_time": 96, "type": "ads_management", "estimated_time_to_regain_access": 120}]})
    limiter.update_from_header("act_1", low)
    assert limiter.check("act_1") == RateLimitStatus.OK
    limiter.update_from_header("act_1", high)
    assert limiter.check("act_1") == RateLimitStatus.BLOCKED


def test_malformed_header_is_ignored(limiter):
    limiter.update_from_header("act_x", "not-json")
    assert limiter.check("act_x") == RateLimitStatus.OK
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_rate_limiter.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement rate_limiter.py**

```python
# gestor-ads/backend/app/meta/rate_limiter.py
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStatus(Enum):
    OK = "ok"
    THROTTLE = "throttle"
    BLOCKED = "blocked"


@dataclass
class _AccountUsage:
    call_count: int = 0
    total_cputime: int = 0
    total_time: int = 0
    estimated_time_to_regain_access: int = 0


class RateLimiter:
    """Per-account rate limiter using Meta's X-Business-Use-Case-Usage header.

    Thresholds:
      < 75%  → OK
      75-95% → THROTTLE (wait before calling)
      > 95%  → BLOCKED (do not call)
    """

    THROTTLE_THRESHOLD = 75
    BLOCK_THRESHOLD = 95

    def __init__(self, default_throttle_seconds: int = 60):
        self._usage: dict[str, _AccountUsage] = {}
        self._default_throttle = default_throttle_seconds

    def update_from_header(self, act_id: str, header_value: str) -> None:
        """Parse X-Business-Use-Case-Usage JSON and update state for act_id."""
        try:
            data = json.loads(header_value)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Malformed rate limit header for %s, ignoring", act_id)
            return

        entries = data.get(act_id, [])
        if not entries:
            # Try to find the account under any key
            for _key, value in data.items():
                if isinstance(value, list) and value:
                    entries = value
                    break

        if not entries:
            return

        entry = entries[0] if isinstance(entries, list) else entries
        self._usage[act_id] = _AccountUsage(
            call_count=int(entry.get("call_count", 0)),
            total_cputime=int(entry.get("total_cputime", 0)),
            total_time=int(entry.get("total_time", 0)),
            estimated_time_to_regain_access=int(entry.get("estimated_time_to_regain_access", 0)),
        )

    def check(self, act_id: str) -> RateLimitStatus:
        """Check current usage level for the account."""
        usage = self._usage.get(act_id)
        if usage is None:
            return RateLimitStatus.OK

        max_pct = max(usage.call_count, usage.total_cputime, usage.total_time)

        if max_pct > self.BLOCK_THRESHOLD:
            return RateLimitStatus.BLOCKED
        if max_pct >= self.THROTTLE_THRESHOLD:
            return RateLimitStatus.THROTTLE
        return RateLimitStatus.OK

    @property
    def throttle_seconds(self) -> int:
        return self._default_throttle
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_rate_limiter.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/app/meta/rate_limiter.py gestor-ads/backend/tests/unit/test_rate_limiter.py
git commit -m "feat(gestor-ads): rate limiter for Meta Graph API

- Parses X-Business-Use-Case-Usage header per account
- OK < 75%, THROTTLE 75-95%, BLOCKED > 95%
- 7 tests passing"
```

---

### Task 4: Audit Decorator

**Files:**
- Create: `gestor-ads/backend/app/shared/audit.py`
- Test: `gestor-ads/backend/tests/unit/test_audit.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `audit_write(action: str, entity: str)` — decorator factory for async methods on classes that have `_audit_fn` and `_user_id` attributes
  - Calls `self._audit_fn(action, entity, entity_id, request_data, response_data, error)` after the wrapped method

- [ ] **Step 1: Write the failing tests**

```python
# gestor-ads/backend/tests/unit/test_audit.py
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.shared.audit import audit_write


class FakeClient:
    """Simulates MetaAdsClient with _audit_fn and _user_id."""

    def __init__(self, audit_fn=None):
        self._audit_fn = audit_fn
        self._user_id = "user-abc"

    @audit_write(action="create_campaign", entity="campaign")
    async def create_something(self, payload: dict) -> dict:
        return {"id": "123", "status": "PAUSED"}

    @audit_write(action="update_status", entity="campaign")
    async def failing_method(self, payload: dict) -> dict:
        raise ValueError("Meta API exploded")


@pytest.mark.asyncio
async def test_audit_calls_fn_on_success():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    result = await client.create_something({"name": "test"})
    assert result == {"id": "123", "status": "PAUSED"}
    audit_fn.assert_called_once()
    call_kwargs = audit_fn.call_args.kwargs
    assert call_kwargs["action"] == "create_campaign"
    assert call_kwargs["entity"] == "campaign"
    assert call_kwargs["response"] == {"id": "123", "status": "PAUSED"}
    assert call_kwargs["error"] is None


@pytest.mark.asyncio
async def test_audit_calls_fn_on_error():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    with pytest.raises(ValueError, match="exploded"):
        await client.failing_method({"entity_id": "456"})
    audit_fn.assert_called_once()
    call_kwargs = audit_fn.call_args.kwargs
    assert call_kwargs["action"] == "update_status"
    assert call_kwargs["error"] is not None
    assert "exploded" in call_kwargs["error"]


@pytest.mark.asyncio
async def test_audit_skips_if_no_fn():
    client = FakeClient(audit_fn=None)
    result = await client.create_something({"name": "test"})
    assert result == {"id": "123", "status": "PAUSED"}


@pytest.mark.asyncio
async def test_audit_captures_user_id():
    audit_fn = AsyncMock()
    client = FakeClient(audit_fn=audit_fn)
    await client.create_something({"name": "x"})
    assert audit_fn.call_args.kwargs["user_id"] == "user-abc"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_audit.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement audit.py**

```python
# gestor-ads/backend/app/shared/audit.py
from __future__ import annotations

import functools
import logging
from typing import Any

logger = logging.getLogger(__name__)


def audit_write(action: str, entity: str):
    """Decorator for MetaAdsClient write methods.

    Expects the instance (self) to have:
      - _audit_fn: async callable or None
      - _user_id: str

    Calls _audit_fn with action, entity, request, response, error after the method.
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Capture request payload from first positional arg or kwargs
            request_data: Any = None
            if args:
                request_data = args[0]
                if hasattr(request_data, "model_dump"):
                    request_data = request_data.model_dump()
                elif hasattr(request_data, "to_dict"):
                    request_data = request_data.to_dict()
            elif kwargs:
                request_data = dict(kwargs)

            response_data: Any = None
            error_msg: str | None = None

            try:
                response_data = await fn(self, *args, **kwargs)
                return response_data
            except Exception as exc:
                error_msg = str(exc)
                raise
            finally:
                if getattr(self, "_audit_fn", None) is not None:
                    try:
                        await self._audit_fn(
                            user_id=getattr(self, "_user_id", "unknown"),
                            action=action,
                            entity=entity,
                            request=request_data,
                            response=response_data,
                            error=error_msg,
                        )
                    except Exception:
                        logger.exception("Failed to write audit log for %s/%s", action, entity)

        return wrapper

    return decorator
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_audit.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/app/shared/audit.py gestor-ads/backend/tests/unit/test_audit.py
git commit -m "feat(gestor-ads): @audit_write decorator for Meta API writes

- Captures request, response, error, user_id
- Calls _audit_fn if present, skips silently if None
- 4 tests passing"
```

---

### Task 5: Meta Ads Client

**Files:**
- Create: `gestor-ads/backend/app/meta/client.py`
- Create: `gestor-ads/backend/app/meta/schemas.py`
- Test: `gestor-ads/backend/tests/unit/test_meta_client.py`

**Interfaces:**
- Consumes: `RateLimiter` (Task 3), `audit_write` (Task 4), `MetaRateLimitError` / `MetaAPIError` (Task 1)
- Produces:
  - `MetaAdsClient(access_token, act_id, rate_limiter, user_id, audit_fn)` with methods:
    - Read: `get_account_info() -> dict`, `list_campaigns(limit) -> list[dict]`, `get_insights(object_id, date_preset, level) -> list[dict]`, `list_adsets(campaign_id) -> list[dict]`, `list_ads(adset_id) -> list[dict]`
    - Write: `create_campaign(payload) -> dict`, `create_adset(campaign_id, payload) -> dict`, `create_ad(adset_id, creative_id, payload) -> dict`, `upload_image(file_bytes, filename) -> dict`, `update_status(entity_id, status) -> dict`
    - Internal: `_request(method, path, **kwargs) -> dict`, `_extract_metric(items, match_terms) -> float`
  - Pydantic schemas: `CampaignCreatePayload`, `AdSetPayload`, `AdPayload`

- [ ] **Step 1: Write the failing tests for _extract_metric and _request**

```python
# gestor-ads/backend/tests/unit/test_meta_client.py
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.meta.client import MetaAdsClient
from app.meta.rate_limiter import RateLimiter
from app.shared.exceptions import MetaAPIError, MetaRateLimitError


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter()


@pytest.fixture
def client(limiter) -> MetaAdsClient:
    return MetaAdsClient(
        access_token="test-token",
        act_id="act_123",
        rate_limiter=limiter,
        user_id="user-1",
        audit_fn=AsyncMock(),
    )


# --- _extract_metric (migrated from campaign_optimizer) ---


def test_extract_metric_finds_leads():
    actions = [
        {"action_type": "link_click", "value": "50"},
        {"action_type": "messaging_conversation_started", "value": "7"},
        {"action_type": "lead", "value": "3"},
    ]
    result = MetaAdsClient._extract_metric(actions, ("messaging_conversation_started", "lead", "contact", "omni_lead"))
    assert result == 10.0


def test_extract_metric_returns_zero_for_none():
    assert MetaAdsClient._extract_metric(None, ("lead",)) == 0.0


def test_extract_metric_returns_zero_for_empty():
    assert MetaAdsClient._extract_metric([], ("lead",)) == 0.0


def test_extract_metric_handles_bad_value():
    actions = [{"action_type": "lead", "value": "not-a-number"}]
    assert MetaAdsClient._extract_metric(actions, ("lead",)) == 0.0


# --- _request ---


@pytest.mark.asyncio
@respx.mock
async def test_request_success(client):
    route = respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            200,
            json={"id": "act_123", "name": "Test Account"},
            headers={"X-Business-Use-Case-Usage": json.dumps({"act_123": [{"call_count": 5, "total_cputime": 5, "total_time": 5, "type": "ads_management", "estimated_time_to_regain_access": 0}]})},
        )
    )
    result = await client._request("GET", "/act_123")
    assert result == {"id": "act_123", "name": "Test Account"}
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_request_meta_error(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            400,
            json={"error": {"message": "Invalid token", "code": 190, "error_subcode": 463}},
        )
    )
    with pytest.raises(MetaAPIError, match="Invalid token"):
        await client._request("GET", "/act_123")


@pytest.mark.asyncio
@respx.mock
async def test_request_rate_limit_error(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(
            400,
            json={"error": {"message": "limit reached", "code": 4, "error_subcode": 17}},
        )
    )
    with pytest.raises(MetaRateLimitError):
        await client._request("GET", "/act_123")


# --- Read methods ---


@pytest.mark.asyncio
@respx.mock
async def test_get_account_info(client):
    respx.get("https://graph.facebook.com/v23.0/act_123").mock(
        return_value=httpx.Response(200, json={"id": "act_123", "name": "Conta", "account_status": 1, "currency": "BRL", "timezone_name": "America/Sao_Paulo"})
    )
    info = await client.get_account_info()
    assert info["name"] == "Conta"
    assert info["currency"] == "BRL"


@pytest.mark.asyncio
@respx.mock
async def test_list_campaigns(client):
    respx.get("https://graph.facebook.com/v23.0/act_123/campaigns").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "c1", "name": "Camp 1"}, {"id": "c2", "name": "Camp 2"}], "paging": {}},
        )
    )
    camps = await client.list_campaigns()
    assert len(camps) == 2
    assert camps[0]["name"] == "Camp 1"


@pytest.mark.asyncio
@respx.mock
async def test_get_insights(client):
    respx.get("https://graph.facebook.com/v23.0/act_123/insights").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "impressions": "1000",
                        "clicks": "50",
                        "spend": "100.00",
                        "ctr": "5.0",
                        "cpc": "2.0",
                        "cpm": "100.0",
                        "frequency": "1.5",
                        "reach": "800",
                        "actions": [{"action_type": "lead", "value": "5"}],
                        "cost_per_action_type": [{"action_type": "lead", "value": "20.0"}],
                    }
                ],
                "paging": {},
            },
        )
    )
    data = await client.get_insights("act_123")
    assert len(data) == 1
    assert data[0]["spend"] == "100.00"


# --- Write methods ---


@pytest.mark.asyncio
@respx.mock
async def test_create_campaign_forces_paused(client):
    respx.post("https://graph.facebook.com/v23.0/act_123/campaigns").mock(
        return_value=httpx.Response(200, json={"id": "999"})
    )
    result = await client.create_campaign(
        name="[TEST] | leads | sp | 20260827-1400",
        objective="OUTCOME_LEADS",
        special_ad_categories=[],
        daily_budget_cents=5000,
    )
    assert result == {"id": "999"}
    # Verify the request sent status=PAUSED
    sent = respx.calls[0].request
    assert b"PAUSED" in sent.content


@pytest.mark.asyncio
@respx.mock
async def test_update_status(client):
    respx.post("https://graph.facebook.com/v23.0/campaign_555").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await client.update_status("campaign_555", "ACTIVE")
    assert result["success"] is True


@pytest.mark.asyncio
@respx.mock
async def test_upload_image(client):
    respx.post("https://graph.facebook.com/v23.0/act_123/adimages").mock(
        return_value=httpx.Response(200, json={"images": {"image.jpg": {"hash": "abc123"}}})
    )
    result = await client.upload_image(b"fake-image-bytes", "image.jpg")
    assert "images" in result
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_meta_client.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement schemas.py**

```python
# gestor-ads/backend/app/meta/schemas.py
from __future__ import annotations

from pydantic import BaseModel


class CampaignCreatePayload(BaseModel):
    name: str
    objective: str
    special_ad_categories: list[str] = []
    daily_budget_cents: int | None = None
    lifetime_budget_cents: int | None = None


class AdSetPayload(BaseModel):
    name: str
    daily_budget_cents: int | None = None
    targeting: dict = {}
    optimization_goal: str = "LEAD_GENERATION"
    billing_event: str = "IMPRESSIONS"
    start_time: str | None = None
    end_time: str | None = None


class AdPayload(BaseModel):
    name: str
    status: str = "PAUSED"
```

- [ ] **Step 4: Implement client.py**

```python
# gestor-ads/backend/app/meta/client.py
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from app.meta.rate_limiter import RateLimiter, RateLimitStatus
from app.shared.audit import audit_write
from app.shared.exceptions import MetaAPIError, MetaRateLimitError

logger = logging.getLogger(__name__)

_RATE_LIMIT_CODES = {4, 17, 32, 613}


class MetaAdsClient:
    """Client for Meta Marketing API v23.0 — read and write."""

    BASE = "https://graph.facebook.com/v23.0"

    def __init__(
        self,
        access_token: str,
        act_id: str,
        rate_limiter: RateLimiter,
        user_id: str = "",
        audit_fn=None,
    ):
        self.token = access_token
        self.act_id = act_id
        self.limiter = rate_limiter
        self._user_id = user_id
        self._audit_fn = audit_fn
        self._http = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self._http.aclose()

    # === INTERNAL ===

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Central request method with rate limiting and error handling."""
        status = self.limiter.check(self.act_id)
        if status == RateLimitStatus.BLOCKED:
            raise MetaRateLimitError(
                f"Rate limit atingido para {self.act_id}. Aguarde.",
                meta={"retry_after_seconds": self.limiter.throttle_seconds, "account": self.act_id},
            )
        if status == RateLimitStatus.THROTTLE:
            await asyncio.sleep(self.limiter.throttle_seconds)

        url = f"{self.BASE}{path}"

        # Inject access_token
        if method.upper() == "GET":
            params = kwargs.get("params", {})
            params["access_token"] = self.token
            kwargs["params"] = params
        else:
            data = kwargs.get("data", {})
            if isinstance(data, dict):
                data["access_token"] = self.token
                kwargs["data"] = data

        response = await self._http.request(method, url, **kwargs)

        # Update rate limiter from header
        usage_header = response.headers.get("X-Business-Use-Case-Usage", "")
        if usage_header:
            self.limiter.update_from_header(self.act_id, usage_header)

        result = response.json()

        if "error" in result:
            error = result["error"]
            code = error.get("code", 0)
            subcode = error.get("error_subcode", 0)
            message = error.get("message", "Meta API error")

            if code in _RATE_LIMIT_CODES or subcode in _RATE_LIMIT_CODES:
                raise MetaRateLimitError(
                    message,
                    meta={"retry_after_seconds": self.limiter.throttle_seconds, "account": self.act_id},
                )
            raise MetaAPIError(message, meta={"code": code, "subcode": subcode})

        return result

    @staticmethod
    def _extract_metric(items: list[dict[str, Any]] | None, match_terms: tuple[str, ...]) -> float:
        """Extract metric value from Meta actions array.

        Migrated from campaign_optimizer/connectors/meta_ads.py — proven logic.
        Searches for action_types matching any of the match_terms.
        """
        if not items:
            return 0.0
        total = 0.0
        for item in items:
            action_type = str(item.get("action_type", "")).lower()
            if any(term in action_type for term in match_terms):
                try:
                    total += float(item.get("value", 0) or 0)
                except (TypeError, ValueError):
                    continue
        return total

    # === READ ===

    async def get_account_info(self) -> dict:
        """Returns account id, name, status, currency, timezone."""
        return await self._request(
            "GET",
            f"/{self.act_id}",
            params={"fields": "id,name,account_status,currency,timezone_name"},
        )

    async def list_campaigns(self, limit: int = 200) -> list[dict]:
        """List campaigns with automatic pagination (max 10 pages)."""
        all_campaigns: list[dict] = []
        params = {
            "fields": "id,name,objective,status,daily_budget,lifetime_budget,effective_status",
            "limit": str(limit),
        }
        path = f"/{self.act_id}/campaigns"
        next_path: str | None = path
        next_params: dict | None = params
        page = 0

        while next_path and page < 10:
            data = await self._request("GET", next_path, params=next_params or {})
            all_campaigns.extend(data.get("data", []))
            paging = data.get("paging", {})
            next_url = paging.get("next")
            if next_url:
                # Extract path from full URL
                next_path = next_url.replace(self.BASE, "")
                next_params = None  # params are in the URL
            else:
                next_path = None
            page += 1

        return all_campaigns

    async def get_insights(
        self,
        object_id: str,
        date_preset: str = "last_7d",
        level: str = "campaign",
    ) -> list[dict]:
        """Fetch aggregated metrics for an account or object."""
        fields = ",".join([
            "campaign_name", "adset_name", "ad_name",
            "impressions", "reach", "clicks", "ctr", "cpc", "cpm",
            "spend", "frequency",
            "actions", "cost_per_action_type",
            "date_start", "date_stop",
        ])
        data = await self._request(
            "GET",
            f"/{object_id}/insights",
            params={"fields": fields, "date_preset": date_preset, "level": level, "limit": "200"},
        )
        return data.get("data", [])

    async def list_adsets(self, campaign_id: str) -> list[dict]:
        data = await self._request(
            "GET",
            f"/{campaign_id}/adsets",
            params={"fields": "id,name,status,daily_budget,targeting,optimization_goal"},
        )
        return data.get("data", [])

    async def list_ads(self, adset_id: str) -> list[dict]:
        data = await self._request(
            "GET",
            f"/{adset_id}/ads",
            params={"fields": "id,name,status,creative"},
        )
        return data.get("data", [])

    # === WRITE ===

    @audit_write(action="create_campaign", entity="campaign")
    async def create_campaign(
        self,
        name: str,
        objective: str,
        special_ad_categories: list[str] | None = None,
        daily_budget_cents: int | None = None,
        lifetime_budget_cents: int | None = None,
    ) -> dict:
        """Create campaign — ALWAYS with status=PAUSED."""
        payload: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": json.dumps(special_ad_categories or []),
        }
        if daily_budget_cents is not None:
            payload["daily_budget"] = str(daily_budget_cents)
        if lifetime_budget_cents is not None:
            payload["lifetime_budget"] = str(lifetime_budget_cents)

        return await self._request("POST", f"/{self.act_id}/campaigns", data=payload)

    @audit_write(action="create_adset", entity="adset")
    async def create_adset(self, campaign_id: str, payload: dict) -> dict:
        data = {
            "campaign_id": campaign_id,
            "status": "PAUSED",
            **payload,
        }
        return await self._request("POST", f"/{self.act_id}/adsets", data=data)

    @audit_write(action="create_ad", entity="ad")
    async def create_ad(self, adset_id: str, creative_id: str, payload: dict) -> dict:
        data = {
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": "PAUSED",
            **payload,
        }
        return await self._request("POST", f"/{self.act_id}/ads", data=data)

    @audit_write(action="upload_image", entity="creative")
    async def upload_image(self, file_bytes: bytes, filename: str) -> dict:
        return await self._request(
            "POST",
            f"/{self.act_id}/adimages",
            data={"access_token": self.token},
            files={"filename": (filename, file_bytes)},
        )

    @audit_write(action="update_status", entity="campaign")
    async def update_status(self, entity_id: str, status: str) -> dict:
        """Change entity status (ACTIVE, PAUSED)."""
        return await self._request("POST", f"/{entity_id}", data={"status": status})
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/unit/test_meta_client.py -v
```

Expected: all passed

- [ ] **Step 6: Commit**

```bash
git add gestor-ads/backend/app/meta/client.py gestor-ads/backend/app/meta/schemas.py
git add gestor-ads/backend/tests/unit/test_meta_client.py
git commit -m "feat(gestor-ads): MetaAdsClient with read + write + rate limiting

- Read: get_account_info, list_campaigns, get_insights, list_adsets, list_ads
- Write: create_campaign (PAUSED), create_adset, create_ad, upload_image, update_status
- _extract_metric migrated from campaign_optimizer (proven logic)
- _request: rate limit check, header parsing, error hierarchy
- All writes audited via @audit_write
- 14 tests passing"
```

---

### Task 6: Rules Engine

**Files:**
- Create: `gestor-ads/backend/app/core/__init__.py`
- Create: `gestor-ads/backend/app/core/rules.py`
- Test: `gestor-ads/backend/tests/unit/test_rules.py`

**Interfaces:**
- Consumes: nothing (pure functions)
- Produces:
  - `RuleResult` dataclass: `severity`, `rule_name`, `action`, `campaign`, `entity_level`, `entity_name`, `reason`, `should_pause`, `meta_entity_id`
  - `AccountThresholds` dataclass: `target_cpl`, `waste_limit`, `min_ctr`, `max_frequency`
  - `evaluate(metrics: list[dict], thresholds: AccountThresholds) -> list[RuleResult]`

- [ ] **Step 1: Write the failing tests**

```python
# gestor-ads/backend/tests/unit/test_rules.py
from __future__ import annotations

from app.core.rules import AccountThresholds, RuleResult, evaluate


def _thresholds(**overrides) -> AccountThresholds:
    defaults = {"target_cpl": 40.0, "waste_limit": 100.0, "min_ctr": 0.8, "max_frequency": 3.0}
    defaults.update(overrides)
    return AccountThresholds(**defaults)


def _row(**overrides) -> dict:
    base = {
        "campaign": "Test Campaign",
        "entity_level": "campaign",
        "entity_name": "Test Campaign",
        "meta_entity_id": "c_123",
        "spend": 0,
        "leads": 0,
        "ctr": 0,
        "cpl": 0,
        "frequency": 0,
        "impressions": 0,
        "effective_status": "ACTIVE",
    }
    base.update(overrides)
    return base


def test_gasto_sem_lead():
    """R$ 150 gastos, 0 leads → vermelho, pausar."""
    rows = [_row(spend=150, leads=0)]
    results = evaluate(rows, _thresholds())
    red = [r for r in results if r.rule_name == "gasto_sem_lead"]
    assert len(red) == 1
    assert red[0].severity == "vermelho"
    assert red[0].should_pause is True
    assert "150" in red[0].reason


def test_gasto_sem_lead_below_limit():
    """R$ 50 gastos, 0 leads but below waste_limit → no alert."""
    rows = [_row(spend=50, leads=0)]
    results = evaluate(rows, _thresholds(waste_limit=100))
    assert not any(r.rule_name == "gasto_sem_lead" for r in results)


def test_cpl_acima_meta():
    """CPL R$ 60 when target is R$ 40 (30% margin = 52) → amarelo."""
    rows = [_row(leads=5, cpl=60)]
    results = evaluate(rows, _thresholds(target_cpl=40))
    yellow = [r for r in results if r.rule_name == "cpl_acima_meta"]
    assert len(yellow) == 1
    assert yellow[0].severity == "amarelo"


def test_cpl_within_margin():
    """CPL R$ 50 when target is R$ 40 (margin at 52) → no alert."""
    rows = [_row(leads=5, cpl=50)]
    results = evaluate(rows, _thresholds(target_cpl=40))
    assert not any(r.rule_name == "cpl_acima_meta" for r in results)


def test_ctr_baixo():
    """CTR 0.5% below min 0.8% → amarelo."""
    rows = [_row(ctr=0.5)]
    results = evaluate(rows, _thresholds(min_ctr=0.8))
    low_ctr = [r for r in results if r.rule_name == "ctr_baixo"]
    assert len(low_ctr) == 1
    assert low_ctr[0].action == "trocar_criativo_ou_copy"


def test_frequencia_alta():
    """Frequency 4.5 above max 3.0 → amarelo."""
    rows = [_row(frequency=4.5)]
    results = evaluate(rows, _thresholds(max_frequency=3.0))
    freq = [r for r in results if r.rule_name == "frequencia_alta"]
    assert len(freq) == 1
    assert freq[0].action == "trocar_criativo_ou_publico"


def test_sem_impressao():
    """Spend > 0 but impressions = 0 → vermelho."""
    rows = [_row(spend=50, impressions=0)]
    results = evaluate(rows, _thresholds())
    no_imp = [r for r in results if r.rule_name == "sem_impressao"]
    assert len(no_imp) == 1
    assert no_imp[0].severity == "vermelho"


def test_criativo_reprovado():
    """effective_status = DISAPPROVED → vermelho."""
    rows = [_row(effective_status="DISAPPROVED")]
    results = evaluate(rows, _thresholds())
    disap = [r for r in results if r.rule_name == "criativo_reprovado"]
    assert len(disap) == 1
    assert disap[0].severity == "vermelho"
    assert disap[0].action == "trocar_criativo"


def test_healthy_campaign_no_alerts():
    rows = [_row(spend=80, leads=5, cpl=16, ctr=2.5, frequency=1.2, impressions=5000)]
    results = evaluate(rows, _thresholds())
    assert len(results) == 0


def test_multiple_rules_fire():
    """One row triggers multiple rules."""
    rows = [_row(spend=200, leads=0, ctr=0.3, frequency=5.0, impressions=1000)]
    results = evaluate(rows, _thresholds())
    names = {r.rule_name for r in results}
    assert "gasto_sem_lead" in names
    assert "ctr_baixo" in names
    assert "frequencia_alta" in names


def test_results_have_meta_entity_id():
    rows = [_row(spend=150, leads=0, meta_entity_id="c_999")]
    results = evaluate(rows, _thresholds())
    assert results[0].meta_entity_id == "c_999"


def test_results_sorted_by_severity():
    """vermelho before amarelo."""
    rows = [_row(spend=150, leads=0, ctr=0.5, impressions=1000)]
    results = evaluate(rows, _thresholds())
    severities = [r.severity for r in results]
    assert severities.index("vermelho") < severities.index("amarelo")
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_rules.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement rules.py**

Create `gestor-ads/backend/app/core/__init__.py` (empty).

```python
# gestor-ads/backend/app/core/rules.py
"""Rule engine for campaign optimization.

Migrated from campaign_optimizer/core/rules.py and expanded with 2 new rules.
Thresholds come from ad_accounts (database), not hardcoded dicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field

_SEVERITY_ORDER = {"vermelho": 0, "amarelo": 1, "verde": 2}


@dataclass
class RuleResult:
    severity: str
    rule_name: str
    action: str
    campaign: str
    entity_level: str
    entity_name: str
    reason: str
    should_pause: bool = False
    meta_entity_id: str | None = None


@dataclass
class AccountThresholds:
    """Per-account thresholds — stored in ad_accounts table."""

    target_cpl: float = 0.0
    waste_limit: float = 100.0
    min_ctr: float = 0.8
    max_frequency: float = 3.0


def evaluate(metrics: list[dict], thresholds: AccountThresholds) -> list[RuleResult]:
    """Run all rules against metrics and return results sorted by severity (vermelho first)."""
    results: list[RuleResult] = []

    for row in metrics:
        spend = float(row.get("spend") or 0)
        leads = int(row.get("leads") or 0)
        ctr = float(row.get("ctr") or 0)
        cpl = float(row.get("cpl") or 0)
        frequency = float(row.get("frequency") or 0)
        impressions = int(row.get("impressions") or 0)
        effective_status = str(row.get("effective_status", "")).upper()

        campaign = row.get("campaign", "Campanha sem nome")
        entity_name = row.get("entity_name", campaign)
        entity_level = row.get("entity_level", "campaign")
        meta_id = row.get("meta_entity_id")

        # Rule 1: gasto sem lead (migrated)
        if spend >= thresholds.waste_limit and leads == 0:
            results.append(RuleResult(
                severity="vermelho",
                rule_name="gasto_sem_lead",
                action="pausar",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason=f"Gastou R$ {spend:.2f} sem gerar lead. Limite: R$ {thresholds.waste_limit:.2f}.",
                should_pause=True,
                meta_entity_id=meta_id,
            ))

        # Rule 2: CPL acima da meta (migrated, with 30% margin)
        margin = thresholds.target_cpl * 1.3
        if thresholds.target_cpl > 0 and leads > 0 and cpl > margin:
            results.append(RuleResult(
                severity="amarelo",
                rule_name="cpl_acima_meta",
                action="revisar",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason=f"CPL em R$ {cpl:.2f}, acima de R$ {margin:.2f} (meta + 30%).",
                meta_entity_id=meta_id,
            ))

        # Rule 3: CTR baixo (migrated)
        if ctr > 0 and ctr < thresholds.min_ctr:
            results.append(RuleResult(
                severity="amarelo",
                rule_name="ctr_baixo",
                action="trocar_criativo_ou_copy",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason=f"CTR em {ctr:.2f}%, abaixo do mínimo de {thresholds.min_ctr:.2f}%.",
                meta_entity_id=meta_id,
            ))

        # Rule 4: Frequência alta (migrated)
        if frequency > thresholds.max_frequency:
            results.append(RuleResult(
                severity="amarelo",
                rule_name="frequencia_alta",
                action="trocar_criativo_ou_publico",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason=f"Frequência em {frequency:.2f}, acima do limite de {thresholds.max_frequency:.2f}.",
                meta_entity_id=meta_id,
            ))

        # Rule 5: Sem impressão (new)
        if spend > 0 and impressions == 0:
            results.append(RuleResult(
                severity="vermelho",
                rule_name="sem_impressao",
                action="revisar_conta",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason=f"Gastou R$ {spend:.2f} mas registrou 0 impressões. Verificar conta/campanha.",
                meta_entity_id=meta_id,
            ))

        # Rule 6: Criativo reprovado (new)
        if effective_status == "DISAPPROVED":
            results.append(RuleResult(
                severity="vermelho",
                rule_name="criativo_reprovado",
                action="trocar_criativo",
                campaign=campaign,
                entity_level=entity_level,
                entity_name=entity_name,
                reason="Criativo reprovado pela Meta. Substitua para a campanha voltar a rodar.",
                meta_entity_id=meta_id,
            ))

    results.sort(key=lambda r: _SEVERITY_ORDER.get(r.severity, 99))
    return results
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_rules.py -v
```

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/app/core/
git add gestor-ads/backend/tests/unit/test_rules.py
git commit -m "feat(gestor-ads): rules engine with 6 rules (4 migrated + 2 new)

- gasto_sem_lead, cpl_acima_meta (30% margin), ctr_baixo, frequencia_alta: migrated
- sem_impressao, criativo_reprovado: new
- AccountThresholds from DB, not hardcoded
- Results sorted by severity (vermelho first)
- 12 tests passing"
```

---

### Task 7: KPI Aggregator + Naming Convention

**Files:**
- Create: `gestor-ads/backend/app/core/kpis.py`
- Create: `gestor-ads/backend/app/core/naming.py`
- Test: `gestor-ads/backend/tests/unit/test_kpis.py`
- Test: `gestor-ads/backend/tests/unit/test_naming.py`

**Interfaces:**
- Consumes: nothing (pure functions)
- Produces:
  - `KPISummary` dataclass: `total_spend`, `total_leads`, `total_clicks`, `total_impressions`, `cpl_medio`, `cpc_medio`, `ctr_medio`, `melhor_campanha`, `pior_campanha`, `tendencia`
  - `summarize_kpis(metrics: list[dict]) -> KPISummary`
  - `campaign_name(marca, objetivo, publico) -> str`
  - `adset_name(marca, segmento) -> str`
  - `ad_name(marca, criativo) -> str`

- [ ] **Step 1: Write the failing tests for KPIs**

```python
# gestor-ads/backend/tests/unit/test_kpis.py
from __future__ import annotations

from app.core.kpis import KPISummary, summarize_kpis


def _row(campaign="Camp", spend=0, leads=0, clicks=0, impressions=0, **kw):
    return {"campaign": campaign, "spend": spend, "leads": leads, "clicks": clicks, "impressions": impressions, **kw}


def test_basic_aggregation():
    rows = [
        _row(spend=100, leads=5, clicks=50, impressions=1000),
        _row(spend=200, leads=10, clicks=100, impressions=2000),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.total_spend == 300
    assert kpi.total_leads == 15
    assert kpi.total_clicks == 150
    assert kpi.total_impressions == 3000
    assert kpi.cpl_medio == 20.0
    assert kpi.cpc_medio == 2.0
    assert kpi.ctr_medio == 5.0


def test_zero_leads_cpl_is_zero():
    rows = [_row(spend=100, leads=0, clicks=10, impressions=500)]
    kpi = summarize_kpis(rows)
    assert kpi.cpl_medio == 0


def test_empty_rows():
    kpi = summarize_kpis([])
    assert kpi.total_spend == 0
    assert kpi.total_leads == 0
    assert kpi.melhor_campanha is None
    assert kpi.pior_campanha is None
    assert kpi.tendencia == "estavel"


def test_melhor_pior_campanha():
    rows = [
        _row(campaign="Best", spend=100, leads=10, clicks=50, impressions=1000),
        _row(campaign="Worst", spend=200, leads=2, clicks=20, impressions=500),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.melhor_campanha == "Best"
    assert kpi.pior_campanha == "Worst"


def test_tendencia_subindo():
    """First half worse than second half → subindo."""
    rows = [
        _row(campaign="A", spend=100, leads=2, clicks=20, impressions=500, date="2026-08-20"),
        _row(campaign="A", spend=100, leads=8, clicks=80, impressions=500, date="2026-08-25"),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.tendencia == "subindo"


def test_tendencia_caindo():
    """First half better than second half → caindo."""
    rows = [
        _row(campaign="A", spend=100, leads=10, clicks=80, impressions=500, date="2026-08-20"),
        _row(campaign="A", spend=100, leads=1, clicks=5, impressions=500, date="2026-08-25"),
    ]
    kpi = summarize_kpis(rows)
    assert kpi.tendencia == "caindo"
```

- [ ] **Step 2: Write the failing tests for naming**

```python
# gestor-ads/backend/tests/unit/test_naming.py
from __future__ import annotations

import re

from app.core.naming import ad_name, adset_name, campaign_name


def test_campaign_name_format():
    name = campaign_name("FORTEC", "leads-whatsapp", "sp-25-45-imoveis")
    assert name.startswith("[FORTEC]")
    assert "leads-whatsapp" in name
    assert "sp-25-45-imoveis" in name
    # Ends with AAAAMMDD-HHMM
    assert re.search(r"\d{8}-\d{4}$", name)


def test_adset_name_format():
    name = adset_name("FORTEC", "homens-30-45-sp")
    assert name.startswith("[FORTEC]")
    assert "homens-30-45-sp" in name
    assert re.search(r"\d{8}-\d{4}$", name)


def test_ad_name_format():
    name = ad_name("FORTEC", "video-prova-social")
    assert name.startswith("[FORTEC]")
    assert "video-prova-social" in name
    assert re.search(r"\d{8}-\d{4}$", name)


def test_campaign_name_pipe_separator():
    name = campaign_name("X", "obj", "pub")
    parts = name.split(" | ")
    assert len(parts) == 3
    assert parts[0] == "[X]"
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
pytest tests/unit/test_kpis.py tests/unit/test_naming.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 4: Implement kpis.py**

```python
# gestor-ads/backend/app/core/kpis.py
"""KPI aggregator — migrated from campaign_optimizer/core/rules.py summarize_kpis().

Expanded with: melhor/pior campanha, tendência.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KPISummary:
    total_spend: float
    total_leads: int
    total_clicks: int
    total_impressions: int
    cpl_medio: float
    cpc_medio: float
    ctr_medio: float
    melhor_campanha: str | None
    pior_campanha: str | None
    tendencia: str  # 'subindo' | 'estavel' | 'caindo'


def summarize_kpis(metrics: list[dict]) -> KPISummary:
    """Aggregate metrics for a period."""
    if not metrics:
        return KPISummary(
            total_spend=0, total_leads=0, total_clicks=0, total_impressions=0,
            cpl_medio=0, cpc_medio=0, ctr_medio=0,
            melhor_campanha=None, pior_campanha=None, tendencia="estavel",
        )

    total_spend = sum(float(r.get("spend") or 0) for r in metrics)
    total_leads = sum(int(r.get("leads") or 0) for r in metrics)
    total_clicks = sum(int(r.get("clicks") or 0) for r in metrics)
    total_impressions = sum(int(r.get("impressions") or 0) for r in metrics)

    cpl = round(total_spend / total_leads, 2) if total_leads else 0
    cpc = round(total_spend / total_clicks, 2) if total_clicks else 0
    ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions else 0

    # Best / worst campaign by CPL (lower is better, must have leads)
    by_campaign: dict[str, dict] = {}
    for r in metrics:
        name = r.get("campaign", "?")
        if name not in by_campaign:
            by_campaign[name] = {"spend": 0, "leads": 0}
        by_campaign[name]["spend"] += float(r.get("spend") or 0)
        by_campaign[name]["leads"] += int(r.get("leads") or 0)

    campaigns_with_leads = {
        k: v for k, v in by_campaign.items() if v["leads"] > 0
    }
    melhor = None
    pior = None
    if campaigns_with_leads:
        melhor = min(campaigns_with_leads, key=lambda k: campaigns_with_leads[k]["spend"] / campaigns_with_leads[k]["leads"])
        pior = max(campaigns_with_leads, key=lambda k: campaigns_with_leads[k]["spend"] / campaigns_with_leads[k]["leads"])
    elif by_campaign:
        # No leads anywhere — worst is whoever spent the most
        pior = max(by_campaign, key=lambda k: by_campaign[k]["spend"])

    # Trend: compare first half vs second half by lead rate
    half = len(metrics) // 2
    if half > 0:
        first_leads = sum(int(r.get("leads") or 0) for r in metrics[:half])
        second_leads = sum(int(r.get("leads") or 0) for r in metrics[half:])
        if second_leads > first_leads * 1.2:
            tendencia = "subindo"
        elif first_leads > second_leads * 1.2:
            tendencia = "caindo"
        else:
            tendencia = "estavel"
    else:
        tendencia = "estavel"

    return KPISummary(
        total_spend=round(total_spend, 2),
        total_leads=total_leads,
        total_clicks=total_clicks,
        total_impressions=total_impressions,
        cpl_medio=cpl,
        cpc_medio=cpc,
        ctr_medio=ctr,
        melhor_campanha=melhor,
        pior_campanha=pior,
        tendencia=tendencia,
    )
```

- [ ] **Step 5: Implement naming.py**

```python
# gestor-ads/backend/app/core/naming.py
"""Standardized naming convention for Meta Ads entities.

Pattern: [MARCA] | objetivo | publico | AAAAMMDD-HHMM
"""
from __future__ import annotations

from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def campaign_name(marca: str, objetivo: str, publico: str) -> str:
    """[MARCA] | objetivo | publico | AAAAMMDD-HHMM"""
    return f"[{marca}] | {objetivo} | {publico} | {_timestamp()}"


def adset_name(marca: str, segmento: str) -> str:
    """[MARCA] | segmento | AAAAMMDD-HHMM"""
    return f"[{marca}] | {segmento} | {_timestamp()}"


def ad_name(marca: str, criativo: str) -> str:
    """[MARCA] | criativo | AAAAMMDD-HHMM"""
    return f"[{marca}] | {criativo} | {_timestamp()}"
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest tests/unit/test_kpis.py tests/unit/test_naming.py -v
```

Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add gestor-ads/backend/app/core/kpis.py gestor-ads/backend/app/core/naming.py
git add gestor-ads/backend/tests/unit/test_kpis.py gestor-ads/backend/tests/unit/test_naming.py
git commit -m "feat(gestor-ads): KPI aggregator and naming convention

- summarize_kpis: migrated + added melhor/pior campanha and tendência
- campaign_name, adset_name, ad_name: [MARCA] | ... | AAAAMMDD-HHMM
- 11 tests passing"
```

---

### Task 8: AI Analysis

**Files:**
- Create: `gestor-ads/backend/app/core/analysis.py`
- Test: `gestor-ads/backend/tests/unit/test_analysis.py`

**Interfaces:**
- Consumes: `evaluate()` from Task 6, `summarize_kpis()` from Task 7, `AccountThresholds` from Task 6
- Produces:
  - `AnalysisResult` dataclass: `resumo: str`, `recomendacoes: list[str]`, `acoes: list[dict]`
  - `CampaignBriefing` dataclass: `produto`, `objetivo`, `verba_total`, `dias`, `publico_alvo`, `destino_lead`, `marca`
  - `CampaignStrategy` dataclass: `verba_diaria`, `dias`, `estrutura`, `publico`, `copy`, `justificativa`
  - `fallback_analysis(metrics, alerts) -> str`
  - `analyze_performance(metrics, thresholds, nivel_tecnico, model) -> AnalysisResult`
  - `generate_campaign_strategy(briefing, account_history, nivel_tecnico) -> CampaignStrategy`

- [ ] **Step 1: Write the failing tests**

```python
# gestor-ads/backend/tests/unit/test_analysis.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.analysis import (
    AnalysisResult,
    CampaignBriefing,
    CampaignStrategy,
    analyze_performance,
    fallback_analysis,
    generate_campaign_strategy,
)
from app.core.rules import AccountThresholds


def _row(**kw):
    base = {"campaign": "C1", "spend": 100, "leads": 5, "clicks": 50, "impressions": 1000, "ctr": 5.0, "cpl": 20, "frequency": 1.5, "effective_status": "ACTIVE", "entity_level": "campaign", "entity_name": "C1", "meta_entity_id": "c1"}
    base.update(kw)
    return base


# --- fallback_analysis ---


def test_fallback_no_alerts():
    rows = [_row()]
    result = fallback_analysis(rows, [])
    assert "R$ 100" in result
    assert "5" in result  # leads


def test_fallback_with_red_alerts():
    rows = [_row(spend=200, leads=0)]
    alerts = [{"severity": "vermelho", "rule_name": "gasto_sem_lead"}]
    result = fallback_analysis(rows, alerts)
    assert "critico" in result.lower() or "crítico" in result.lower()


def test_fallback_with_yellow_alerts():
    rows = [_row()]
    alerts = [{"severity": "amarelo", "rule_name": "ctr_baixo"}]
    result = fallback_analysis(rows, alerts)
    assert "alerta" in result.lower()


def test_fallback_zero_leads_warning():
    rows = [_row(spend=50, leads=0)]
    result = fallback_analysis(rows, [])
    assert "lead" in result.lower()


# --- analyze_performance ---


@pytest.mark.asyncio
async def test_analyze_performance_uses_claude():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Análise: CTR ok, CPL bom.")]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_msg)

    with patch("app.core.analysis.anthropic.AsyncAnthropic", return_value=mock_client):
        result = await analyze_performance(
            metrics=[_row()],
            thresholds=AccountThresholds(),
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, AnalysisResult)
    assert "CTR" in result.resumo or "CPL" in result.resumo


@pytest.mark.asyncio
async def test_analyze_performance_fallback_on_error():
    with patch("app.core.analysis.anthropic.AsyncAnthropic", side_effect=Exception("API down")):
        result = await analyze_performance(
            metrics=[_row()],
            thresholds=AccountThresholds(),
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, AnalysisResult)
    assert "R$ 100" in result.resumo  # fallback output


@pytest.mark.asyncio
async def test_analyze_performance_without_api_key():
    result = await analyze_performance(
        metrics=[_row()],
        thresholds=AccountThresholds(),
        nivel_tecnico="leigo",
        anthropic_api_key="",
    )
    assert isinstance(result, AnalysisResult)
    assert result.resumo  # fallback works


# --- generate_campaign_strategy ---


@pytest.mark.asyncio
async def test_generate_strategy():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='{"verba_diaria": 50, "dias": 20, "estrutura": "CBO 2 conjuntos", "publico": "SP 25-45", "copy": "Texto aqui", "justificativa": "Razão"}')]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_msg)

    with patch("app.core.analysis.anthropic.AsyncAnthropic", return_value=mock_client):
        briefing = CampaignBriefing(
            produto="Apartamento alto padrão",
            objetivo="leads-whatsapp",
            verba_total=1000,
            dias=20,
            publico_alvo="homens 30-50 SP",
            destino_lead="whatsapp",
            marca="FORTEC",
        )
        result = await generate_campaign_strategy(
            briefing=briefing,
            account_history=None,
            nivel_tecnico="avancado",
            anthropic_api_key="sk-test",
        )
    assert isinstance(result, CampaignStrategy)
    assert result.verba_diaria > 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/unit/test_analysis.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement analysis.py**

```python
# gestor-ads/backend/app/core/analysis.py
"""AI analysis layer with deterministic fallback.

Migrated from campaign_optimizer/core/ai.py — OpenAI → Claude (Anthropic SDK).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import anthropic

from app.core.kpis import summarize_kpis
from app.core.rules import AccountThresholds, evaluate

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    resumo: str
    recomendacoes: list[str] = field(default_factory=list)
    acoes: list[dict] = field(default_factory=list)


@dataclass
class CampaignBriefing:
    produto: str
    objetivo: str
    verba_total: float
    dias: int
    publico_alvo: str
    destino_lead: str
    marca: str


@dataclass
class CampaignStrategy:
    verba_diaria: float
    dias: int
    estrutura: str
    publico: str
    copy: str
    justificativa: str


# --- Deterministic fallback (migrated from campaign_optimizer) ---


def fallback_analysis(metrics: list[dict], alerts: list[dict]) -> str:
    """Deterministic analysis when Claude is unavailable.

    Priority: gasto sem lead > yellow alerts > no alerts.
    """
    kpis = summarize_kpis(metrics)
    red = [a for a in alerts if a.get("severity") == "vermelho"]
    yellow = [a for a in alerts if a.get("severity") == "amarelo"]

    lines = [
        "Diagnóstico rápido:",
        f"Investimento: R$ {kpis.total_spend:.2f}. Leads: {kpis.total_leads}. CPL médio: R$ {kpis.cpl_medio:.2f}.",
    ]
    if red:
        lines.append(f"Tem {len(red)} ponto(s) crítico(s) queimando dinheiro. Prioridade: pausar ou revisar agora.")
    elif yellow:
        lines.append(f"Sem desperdício grave, mas existem {len(yellow)} alerta(s) para otimizar criativo, público ou copy.")
    else:
        lines.append("Sem alerta crítico nas regras atuais. Acompanhe a consistência dos leads antes de escalar.")

    if kpis.total_leads == 0 and kpis.total_spend > 0:
        lines.append("Atenção: sem conversão registrada. A leitura é de tráfego, não de lead qualificado.")

    lines.append("Próxima ação: resolva primeiro o que gastou sem lead, depois mexa em CTR, frequência e CPL.")
    return "\n".join(lines)


# --- AI-powered analysis ---


async def analyze_performance(
    metrics: list[dict],
    thresholds: AccountThresholds,
    nivel_tecnico: str = "avancado",
    anthropic_api_key: str = "",
    model: str = "claude-sonnet-5",
) -> AnalysisResult:
    """Run rules + KPIs, then send to Claude for analysis.

    nivel_tecnico changes only the prompt language, not the analysis depth.
    Falls back to deterministic analysis if Claude fails.
    """
    alerts = evaluate(metrics, thresholds)
    alerts_dicts = [{"severity": a.severity, "rule_name": a.rule_name, "reason": a.reason, "campaign": a.campaign} for a in alerts]
    kpis = summarize_kpis(metrics)

    if not anthropic_api_key:
        return AnalysisResult(
            resumo=fallback_analysis(metrics, alerts_dicts),
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )

    lang_instruction = (
        "Use termos técnicos (CTR, CPM, CPA, CPL, CBO) normalmente."
        if nivel_tecnico == "avancado"
        else "Traduza toda métrica para consequência prática. Nunca use sigla sem explicar."
    )

    prompt = (
        "Você é analista de tráfego da Creative Agência Marketing. "
        "Escreva em português brasileiro simples, direto e útil. "
        "Não invente números. Explique o que fazer hoje.\n\n"
        f"Nível técnico do usuário: {nivel_tecnico}. {lang_instruction}\n\n"
        f"KPIs: spend={kpis.total_spend}, leads={kpis.total_leads}, "
        f"CPL={kpis.cpl_medio}, CTR={kpis.ctr_medio}%, tendência={kpis.tendencia}\n\n"
        f"Alertas: {json.dumps(alerts_dicts[:20], ensure_ascii=False)}"
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text

        return AnalysisResult(
            resumo=text,
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )

    except Exception as exc:
        logger.warning("Claude analysis failed, using fallback: %s", exc)
        fb = fallback_analysis(metrics, alerts_dicts)
        return AnalysisResult(
            resumo=fb,
            recomendacoes=[a.reason for a in alerts[:5]],
            acoes=[{"entity_id": a.meta_entity_id, "action": a.action} for a in alerts if a.meta_entity_id],
        )


async def generate_campaign_strategy(
    briefing: CampaignBriefing,
    account_history: list[dict] | None = None,
    nivel_tecnico: str = "avancado",
    anthropic_api_key: str = "",
    model: str = "claude-sonnet-5",
) -> CampaignStrategy:
    """Generate a complete campaign strategy with justification."""
    prompt = (
        "Você é gestor de tráfego da Creative Agência Marketing. "
        "Gere uma estratégia completa com justificativa para cada decisão.\n\n"
        f"Produto/serviço: {briefing.produto}\n"
        f"Objetivo: {briefing.objetivo}\n"
        f"Verba total: R$ {briefing.verba_total:.2f}\n"
        f"Prazo: {briefing.dias} dias\n"
        f"Público-alvo: {briefing.publico_alvo}\n"
        f"Destino do lead: {briefing.destino_lead}\n"
        f"Marca: {briefing.marca}\n\n"
        "Responda APENAS com JSON no formato:\n"
        '{"verba_diaria": X, "dias": X, "estrutura": "...", "publico": "...", "copy": "...", "justificativa": "..."}'
    )

    if account_history:
        prompt += f"\n\nHistórico da conta: {json.dumps(account_history[:10], ensure_ascii=False)}"

    try:
        client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text

        # Parse JSON from response (may be wrapped in markdown)
        json_str = text
        if "```" in text:
            json_str = text.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        data = json.loads(json_str.strip())

        return CampaignStrategy(
            verba_diaria=float(data.get("verba_diaria", briefing.verba_total / briefing.dias)),
            dias=int(data.get("dias", briefing.dias)),
            estrutura=data.get("estrutura", "CBO com 2 conjuntos"),
            publico=data.get("publico", briefing.publico_alvo),
            copy=data.get("copy", ""),
            justificativa=data.get("justificativa", ""),
        )

    except Exception as exc:
        logger.warning("Strategy generation failed: %s", exc)
        daily = round(briefing.verba_total / briefing.dias, 2)
        return CampaignStrategy(
            verba_diaria=daily,
            dias=briefing.dias,
            estrutura="CBO com 2 conjuntos de anúncios",
            publico=briefing.publico_alvo,
            copy="",
            justificativa=f"Estratégia padrão: R$ {daily}/dia × {briefing.dias} dias. IA indisponível.",
        )
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/unit/test_analysis.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/app/core/analysis.py gestor-ads/backend/tests/unit/test_analysis.py
git commit -m "feat(gestor-ads): AI analysis with Claude + deterministic fallback

- analyze_performance: rules + KPIs + Claude → AnalysisResult
- generate_campaign_strategy: briefing → CampaignStrategy with justification
- fallback_analysis: migrated from campaign_optimizer (works without API key)
- nivel_tecnico changes language only, not strategy
- 8 tests passing"
```

---

### Task 9: Supabase Migrations

**Files:**
- Create: `gestor-ads/backend/migrations/001_initial_schema.sql`
- Create: `gestor-ads/backend/tests/integration/__init__.py`

**Interfaces:**
- Consumes: nothing
- Produces: 8 tables (profiles, meta_connections, ad_accounts, campaigns, campaign_metrics, campaign_drafts, creatives, audit_log), RLS policies, trigger for new user profile

- [ ] **Step 1: Write the migration SQL**

```sql
-- gestor-ads/backend/migrations/001_initial_schema.sql
-- Gestor Ads — Phase 1 Initial Schema
-- Apply via Supabase MCP or supabase db push

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. profiles — extends auth.users
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL DEFAULT '',
    telefone_e164 TEXT,
    nivel_tecnico TEXT NOT NULL DEFAULT 'avancado'
        CHECK (nivel_tecnico IN ('leigo', 'avancado')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_user_policy" ON profiles FOR ALL USING (id = auth.uid());

-- 2. meta_connections — encrypted OAuth tokens
CREATE TABLE IF NOT EXISTS meta_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meta_user_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    is_valid BOOLEAN NOT NULL DEFAULT true,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, meta_user_id)
);
ALTER TABLE meta_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "meta_connections_user_policy" ON meta_connections FOR ALL USING (user_id = auth.uid());

-- 3. ad_accounts — linked ad accounts
CREATE TABLE IF NOT EXISTS ad_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    connection_id UUID NOT NULL REFERENCES meta_connections(id) ON DELETE CASCADE,
    act_id TEXT NOT NULL,
    nome TEXT NOT NULL DEFAULT '',
    business_id TEXT,
    moeda TEXT NOT NULL DEFAULT 'BRL',
    fuso TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    target_cpl REAL DEFAULT 0,
    waste_limit REAL DEFAULT 100,
    min_ctr REAL DEFAULT 0.8,
    max_frequency REAL DEFAULT 3.0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, act_id)
);
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "ad_accounts_user_policy" ON ad_accounts FOR ALL USING (user_id = auth.uid());

-- 4. campaigns — confirmed on Meta
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meta_campaign_id TEXT NOT NULL,
    nome TEXT NOT NULL,
    objetivo TEXT,
    status TEXT NOT NULL DEFAULT 'PAUSED',
    verba_diaria REAL,
    verba_total REAL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(ad_account_id, meta_campaign_id)
);
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
CREATE POLICY "campaigns_user_policy" ON campaigns FOR ALL USING (user_id = auth.uid());

-- 5. campaign_metrics — daily metrics per campaign
CREATE TABLE IF NOT EXISTS campaign_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    data DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    cpc REAL DEFAULT 0,
    cpm REAL DEFAULT 0,
    frequency REAL DEFAULT 0,
    spend REAL DEFAULT 0,
    leads INTEGER DEFAULT 0,
    cpl REAL DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    raw_json JSONB DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(campaign_id, data)
);
ALTER TABLE campaign_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "campaign_metrics_user_policy" ON campaign_metrics FOR ALL USING (user_id = auth.uid());

-- 6. campaign_drafts — drafts before sending to Meta
CREATE TABLE IF NOT EXISTS campaign_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'rascunho'
        CHECK (status IN ('rascunho', 'aprovado', 'publicando', 'criado', 'erro')),
    meta_campaign_id TEXT,
    erro_detalhes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE campaign_drafts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "campaign_drafts_user_policy" ON campaign_drafts FOR ALL USING (user_id = auth.uid());

-- 7. creatives — stored images/videos
CREATE TABLE IF NOT EXISTS creatives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('image', 'video')),
    storage_path TEXT NOT NULL,
    meta_hash TEXT,
    meta_video_id TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE creatives ENABLE ROW LEVEL SECURITY;
CREATE POLICY "creatives_user_policy" ON creatives FOR ALL USING (user_id = auth.uid());

-- 8. audit_log — all Marketing API writes
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    entidade_id TEXT,
    request JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    origem TEXT NOT NULL DEFAULT 'api',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "audit_log_user_policy" ON audit_log FOR ALL USING (user_id = auth.uid());

-- Trigger: auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, nome)
    VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'nome', ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

- [ ] **Step 2: Create integration test __init__.py**

Create empty `gestor-ads/backend/tests/integration/__init__.py`.

- [ ] **Step 3: Apply migration via Supabase MCP**

Use the Supabase MCP `apply_migration` tool to apply `001_initial_schema.sql` to the project. If no Supabase project is connected yet, create one first with `create_project` or connect manually.

- [ ] **Step 4: Verify tables exist**

Use `list_tables` from Supabase MCP to confirm all 8 tables exist with correct columns.

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/migrations/ gestor-ads/backend/tests/integration/__init__.py
git commit -m "feat(gestor-ads): initial Supabase schema — 8 tables + RLS + trigger

- profiles, meta_connections, ad_accounts, campaigns, campaign_metrics,
  campaign_drafts, creatives, audit_log
- RLS policy on every table: user_id = auth.uid()
- Auto-create profile trigger on auth.users insert"
```

---

### Task 10: Auth Module (Supabase Auth + Meta OAuth)

**Files:**
- Create: `gestor-ads/backend/app/dependencies.py`
- Create: `gestor-ads/backend/app/auth/__init__.py`
- Create: `gestor-ads/backend/app/auth/models.py`
- Create: `gestor-ads/backend/app/auth/meta_oauth.py`
- Create: `gestor-ads/backend/app/auth/router.py`
- Test: `gestor-ads/backend/tests/integration/test_auth_flow.py`

**Interfaces:**
- Consumes: `Settings` (Task 1), `TokenManager` (Task 2), `MetaAdsClient` (Task 5), `RateLimiter` (Task 3)
- Produces:
  - `get_current_user(authorization) -> User` dependency
  - `get_supabase() -> Client` dependency
  - `get_meta_client(user, act_id, supabase) -> MetaAdsClient` dependency
  - Auth router: `POST /register`, `POST /login`, `GET /meta/login`, `GET /meta/callback`
  - `User` model: `id: str`, `email: str`

- [ ] **Step 1: Write auth models**

```python
# gestor-ads/backend/app/auth/models.py
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: str
    password: str
    nome: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str


class User(BaseModel):
    id: str
    email: str


class MetaOAuthURL(BaseModel):
    url: str


class MetaCallbackResponse(BaseModel):
    success: bool
    accounts_found: int
    accounts: list[dict]
```

- [ ] **Step 2: Implement meta_oauth.py**

```python
# gestor-ads/backend/app/auth/meta_oauth.py
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from jose import jwt

from app.config import get_settings


def generate_oauth_url(user_id: str) -> str:
    """Generate Meta OAuth URL with signed state JWT."""
    settings = get_settings()
    state_payload = {
        "user_id": user_id,
        "nonce": secrets.token_hex(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    state = jwt.encode(state_payload, settings.jwt_secret, algorithm="HS256")

    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": "ads_management,ads_read,business_management,pages_show_list",
        "state": state,
        "response_type": "code",
    }
    return f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"


def validate_state(state: str) -> str:
    """Validate state JWT and return user_id. Raises on invalid/expired."""
    settings = get_settings()
    payload = jwt.decode(state, settings.jwt_secret, algorithms=["HS256"])
    return payload["user_id"]
```

- [ ] **Step 3: Implement dependencies.py**

```python
# gestor-ads/backend/app/dependencies.py
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


async def get_meta_client(
    act_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    tm: TokenManager = Depends(get_token_manager),
) -> MetaAdsClient:
    """Build a MetaAdsClient for the given user and ad account."""
    # Find the connection for this account
    account = (
        supabase.table("ad_accounts")
        .select("connection_id")
        .eq("user_id", user.id)
        .eq("act_id", act_id)
        .single()
        .execute()
        .data
    )

    token = await tm.refresh_if_needed(account["connection_id"], supabase)

    async def audit_fn(*, user_id, action, entity, request, response, error):
        supabase.table("audit_log").insert({
            "user_id": user_id,
            "acao": action,
            "entidade": entity,
            "request": request if isinstance(request, dict) else {"raw": str(request)},
            "response": response if isinstance(response, dict) else {"raw": str(response)},
            "origem": "api",
        }).execute()

    return MetaAdsClient(
        access_token=token,
        act_id=act_id,
        rate_limiter=_rate_limiter,
        user_id=user.id,
        audit_fn=audit_fn,
    )
```

- [ ] **Step 4: Implement auth router**

Create `gestor-ads/backend/app/auth/__init__.py` (empty).

```python
# gestor-ads/backend/app/auth/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse

from supabase import Client

from app.auth.meta_oauth import generate_oauth_url, validate_state
from app.auth.models import (
    AuthResponse,
    LoginRequest,
    MetaCallbackResponse,
    MetaOAuthURL,
    RegisterRequest,
    User,
)
from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_supabase, get_token_manager
from app.meta.token_manager import TokenManager
from app.shared.exceptions import AppError

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(
    body: RegisterRequest,
    supabase: Client = Depends(get_supabase),
):
    try:
        result = supabase.auth.sign_up(
            {"email": body.email, "password": body.password, "options": {"data": {"nome": body.nome}}}
        )
        if not result.user:
            raise AppError("Erro ao criar conta", meta={"detail": "Supabase signup failed"})
        return AuthResponse(
            access_token=result.session.access_token if result.session else "",
            user_id=str(result.user.id),
            email=result.user.email or body.email,
        )
    except Exception as exc:
        if isinstance(exc, AppError):
            raise
        raise AppError(f"Erro ao criar conta: {exc}")


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    supabase: Client = Depends(get_supabase),
):
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        return AuthResponse(
            access_token=result.session.access_token,
            user_id=str(result.user.id),
            email=result.user.email or body.email,
        )
    except Exception as exc:
        raise AppError("Email ou senha incorretos", meta={"detail": str(exc)})


@router.get("/meta/login", response_model=MetaOAuthURL)
async def meta_login(user: User = Depends(get_current_user)):
    url = generate_oauth_url(user.id)
    return MetaOAuthURL(url=url)


@router.get("/meta/callback", response_model=MetaCallbackResponse)
async def meta_callback(
    code: str = Query(...),
    state: str = Query(...),
    supabase: Client = Depends(get_supabase),
    tm: TokenManager = Depends(get_token_manager),
):
    # Validate state JWT
    user_id = validate_state(state)

    # Exchange code for long-lived token
    pair = await tm.exchange_code(code)
    encrypted = tm.encrypt(pair.access_token)

    # Get Meta user info
    import httpx

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://graph.facebook.com/v23.0/me",
            params={"access_token": pair.access_token, "fields": "id,name"},
        )
        meta_user = resp.json()

    # Save connection
    supabase.table("meta_connections").upsert(
        {
            "user_id": user_id,
            "meta_user_id": meta_user["id"],
            "access_token_encrypted": encrypted,
            "token_expires_at": pair.expires_at.isoformat(),
            "scopes": ["ads_management", "ads_read", "business_management", "pages_show_list"],
            "is_valid": True,
        },
        on_conflict="user_id,meta_user_id",
    ).execute()

    # Get the connection ID
    conn = (
        supabase.table("meta_connections")
        .select("id")
        .eq("user_id", user_id)
        .eq("meta_user_id", meta_user["id"])
        .single()
        .execute()
        .data
    )

    # List ad accounts
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://graph.facebook.com/v23.0/me/adaccounts",
            params={
                "access_token": pair.access_token,
                "fields": "id,name,account_status,currency,timezone_name,business",
            },
        )
        accounts_data = resp.json().get("data", [])

    # Save ad accounts
    saved_accounts = []
    for acc in accounts_data:
        account_row = {
            "user_id": user_id,
            "connection_id": conn["id"],
            "act_id": acc["id"],
            "nome": acc.get("name", ""),
            "business_id": acc.get("business", {}).get("id", ""),
            "moeda": acc.get("currency", "BRL"),
            "fuso": acc.get("timezone_name", "America/Sao_Paulo"),
            "status": "ACTIVE" if acc.get("account_status") == 1 else "INACTIVE",
        }
        supabase.table("ad_accounts").upsert(
            account_row, on_conflict="user_id,act_id"
        ).execute()
        saved_accounts.append({"act_id": acc["id"], "nome": acc.get("name", "")})

    return MetaCallbackResponse(
        success=True,
        accounts_found=len(saved_accounts),
        accounts=saved_accounts,
    )
```

- [ ] **Step 5: Write integration test for auth**

```python
# gestor-ads/backend/tests/integration/test_auth_flow.py
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.auth.meta_oauth import generate_oauth_url, validate_state


def test_generate_oauth_url_has_required_params():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="test-secret-key-for-testing",
        )
        url = generate_oauth_url("user-uuid-123")
        assert "client_id=12345" in url
        assert "redirect_uri=" in url
        assert "ads_management" in url
        assert "state=" in url


def test_validate_state_round_trip():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="test-secret-key-for-testing",
        )
        url = generate_oauth_url("user-uuid-123")
        state = url.split("state=")[1].split("&")[0]
        user_id = validate_state(state)
        assert user_id == "user-uuid-123"


def test_validate_state_rejects_wrong_secret():
    with patch("app.auth.meta_oauth.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            meta_app_id="12345",
            meta_redirect_uri="https://example.com/callback",
            jwt_secret="original-secret",
        )
        url = generate_oauth_url("user-uuid-123")
        state = url.split("state=")[1].split("&")[0]

        mock_settings.return_value = MagicMock(jwt_secret="different-secret")
        with pytest.raises(Exception):
            validate_state(state)
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
pytest tests/integration/test_auth_flow.py -v
```

Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add gestor-ads/backend/app/auth/ gestor-ads/backend/app/dependencies.py
git add gestor-ads/backend/tests/integration/test_auth_flow.py
git commit -m "feat(gestor-ads): auth module — Supabase Auth + Meta OAuth

- dependencies: get_current_user, get_supabase, get_meta_client
- Auth router: register, login, meta/login, meta/callback
- Meta OAuth: state JWT with 10min expiry, code exchange, account listing
- 3 integration tests passing"
```

---

### Task 11: Campaign + Account Routers

**Files:**
- Create: `gestor-ads/backend/app/campaigns/__init__.py`
- Create: `gestor-ads/backend/app/campaigns/schemas.py`
- Create: `gestor-ads/backend/app/campaigns/router.py`
- Test: `gestor-ads/backend/tests/integration/test_campaign_routers.py`

**Interfaces:**
- Consumes: `get_current_user`, `get_supabase`, `get_meta_client` (Task 10), `MetaAdsClient` (Task 5), `AccountThresholds` (Task 6)
- Produces: Router at `/api` with endpoints: `GET /accounts`, `GET /accounts/{act_id}`, `GET /campaigns`, `GET /campaigns/{id}/insights`, `POST /campaigns/sync`, `POST /campaigns/drafts`, `PATCH /campaigns/drafts/{id}`, `POST /campaigns/drafts/{id}/publish`, `POST /campaigns/{id}/activate`, `POST /campaigns/{id}/pause`

- [ ] **Step 1: Write schemas**

```python
# gestor-ads/backend/app/campaigns/schemas.py
from __future__ import annotations

from pydantic import BaseModel


class AccountOut(BaseModel):
    id: str
    act_id: str
    nome: str
    moeda: str
    fuso: str
    status: str


class CampaignOut(BaseModel):
    id: str
    meta_campaign_id: str
    nome: str
    objetivo: str | None
    status: str
    verba_diaria: float | None
    verba_total: float | None


class SyncRequest(BaseModel):
    act_id: str
    date_preset: str = "last_7d"


class SyncResponse(BaseModel):
    campaigns_synced: int
    metrics_upserted: int
    errors: list[dict]


class DraftCreate(BaseModel):
    act_id: str
    payload: dict


class DraftUpdate(BaseModel):
    payload: dict


class DraftOut(BaseModel):
    id: str
    status: str
    payload: dict
    meta_campaign_id: str | None
    erro_detalhes: str | None
```

- [ ] **Step 2: Implement campaign router**

Create `gestor-ads/backend/app/campaigns/__init__.py` (empty).

```python
# gestor-ads/backend/app/campaigns/router.py
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from supabase import Client

from app.auth.models import User
from app.campaigns.schemas import (
    AccountOut,
    CampaignOut,
    DraftCreate,
    DraftOut,
    DraftUpdate,
    SyncRequest,
    SyncResponse,
)
from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_meta_client, get_supabase
from app.meta.client import MetaAdsClient
from app.shared.exceptions import AppError, CampaignSafetyError, DraftValidationError

router = APIRouter(prefix="/api", tags=["campaigns"])


# === Accounts ===


@router.get("/accounts", response_model=list[AccountOut])
async def list_accounts(
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    rows = (
        supabase.table("ad_accounts")
        .select("id, act_id, nome, moeda, fuso, status")
        .eq("user_id", user.id)
        .execute()
        .data
    )
    return rows


@router.get("/accounts/{act_id}", response_model=AccountOut)
async def get_account(
    act_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    row = (
        supabase.table("ad_accounts")
        .select("id, act_id, nome, moeda, fuso, status")
        .eq("user_id", user.id)
        .eq("act_id", act_id)
        .single()
        .execute()
        .data
    )
    return row


# === Campaigns ===


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    act_id: str | None = None,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    query = supabase.table("campaigns").select("*").eq("user_id", user.id)
    if act_id:
        # Find account ID from act_id
        acc = supabase.table("ad_accounts").select("id").eq("user_id", user.id).eq("act_id", act_id).single().execute().data
        query = query.eq("ad_account_id", acc["id"])
    rows = query.execute().data
    return [
        CampaignOut(
            id=r["id"],
            meta_campaign_id=r["meta_campaign_id"],
            nome=r["nome"],
            objetivo=r.get("objetivo"),
            status=r["status"],
            verba_diaria=r.get("verba_diaria"),
            verba_total=r.get("verba_total"),
        )
        for r in rows
    ]


@router.get("/campaigns/{campaign_id}/insights")
async def campaign_insights(
    campaign_id: str,
    date_preset: str = "last_7d",
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    rows = (
        supabase.table("campaign_metrics")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("user_id", user.id)
        .execute()
        .data
    )
    return rows


# === Sync ===


@router.post("/campaigns/sync", response_model=SyncResponse)
async def sync_campaigns(
    body: SyncRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    meta = await get_meta_client(body.act_id, user, supabase)

    try:
        # Get account ID from DB
        acc = (
            supabase.table("ad_accounts")
            .select("id")
            .eq("user_id", user.id)
            .eq("act_id", body.act_id)
            .single()
            .execute()
            .data
        )
        account_db_id = acc["id"]

        # List campaigns from Meta
        campaigns = await meta.list_campaigns()
        errors = []
        synced = 0
        metrics_count = 0

        for camp in campaigns:
            try:
                # Upsert campaign
                supabase.table("campaigns").upsert(
                    {
                        "ad_account_id": account_db_id,
                        "user_id": user.id,
                        "meta_campaign_id": camp["id"],
                        "nome": camp.get("name", ""),
                        "objetivo": camp.get("objective", ""),
                        "status": camp.get("effective_status", camp.get("status", "UNKNOWN")),
                        "verba_diaria": float(camp.get("daily_budget", 0) or 0) / 100,
                        "verba_total": float(camp.get("lifetime_budget", 0) or 0) / 100,
                        "atualizado_em": datetime.now(timezone.utc).isoformat(),
                    },
                    on_conflict="ad_account_id,meta_campaign_id",
                ).execute()

                # Get local campaign ID
                local = (
                    supabase.table("campaigns")
                    .select("id")
                    .eq("ad_account_id", account_db_id)
                    .eq("meta_campaign_id", camp["id"])
                    .single()
                    .execute()
                    .data
                )

                # Fetch insights
                insights = await meta.get_insights(camp["id"], date_preset=body.date_preset)
                for row in insights:
                    leads = int(MetaAdsClient._extract_metric(
                        row.get("actions"),
                        ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                    ))
                    cpl = MetaAdsClient._extract_metric(
                        row.get("cost_per_action_type"),
                        ("messaging_conversation_started", "lead", "contact", "omni_lead"),
                    )
                    spend = float(row.get("spend", 0) or 0)

                    supabase.table("campaign_metrics").upsert(
                        {
                            "campaign_id": local["id"],
                            "user_id": user.id,
                            "data": row.get("date_start", datetime.now(timezone.utc).date().isoformat()),
                            "impressions": int(float(row.get("impressions", 0) or 0)),
                            "reach": int(float(row.get("reach", 0) or 0)),
                            "clicks": int(float(row.get("clicks", 0) or 0)),
                            "ctr": round(float(row.get("ctr", 0) or 0), 4),
                            "cpc": round(float(row.get("cpc", 0) or 0), 4),
                            "cpm": round(float(row.get("cpm", 0) or 0), 4),
                            "frequency": round(float(row.get("frequency", 0) or 0), 4),
                            "spend": round(spend, 2),
                            "leads": leads,
                            "cpl": round(cpl or (spend / leads if leads else 0), 2),
                            "raw_json": row,
                        },
                        on_conflict="campaign_id,data",
                    ).execute()
                    metrics_count += 1

                synced += 1
            except Exception as exc:
                errors.append({"campaign": camp.get("name", camp["id"]), "error": str(exc)})

        return SyncResponse(campaigns_synced=synced, metrics_upserted=metrics_count, errors=errors)
    finally:
        await meta.close()


# === Drafts ===


@router.post("/campaigns/drafts", response_model=DraftOut)
async def create_draft(
    body: DraftCreate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = (
        supabase.table("ad_accounts")
        .select("id")
        .eq("user_id", user.id)
        .eq("act_id", body.act_id)
        .single()
        .execute()
        .data
    )

    # Validate required fields in payload
    required = ["name", "objective"]
    missing = [f for f in required if f not in body.payload]
    if missing:
        raise DraftValidationError(f"Campos obrigatórios faltando: {', '.join(missing)}")

    row = (
        supabase.table("campaign_drafts")
        .insert({
            "user_id": user.id,
            "ad_account_id": acc["id"],
            "payload": body.payload,
            "status": "rascunho",
        })
        .execute()
        .data[0]
    )
    return DraftOut(
        id=row["id"], status=row["status"], payload=row["payload"],
        meta_campaign_id=row.get("meta_campaign_id"), erro_detalhes=row.get("erro_detalhes"),
    )


@router.patch("/campaigns/drafts/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: str,
    body: DraftUpdate,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    row = (
        supabase.table("campaign_drafts")
        .update({"payload": body.payload, "atualizado_em": datetime.now(timezone.utc).isoformat()})
        .eq("id", draft_id)
        .eq("user_id", user.id)
        .execute()
        .data[0]
    )
    return DraftOut(
        id=row["id"], status=row["status"], payload=row["payload"],
        meta_campaign_id=row.get("meta_campaign_id"), erro_detalhes=row.get("erro_detalhes"),
    )


@router.post("/campaigns/drafts/{draft_id}/publish", response_model=DraftOut)
async def publish_draft(
    draft_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    # Get draft
    draft = (
        supabase.table("campaign_drafts")
        .select("*, ad_accounts!inner(act_id, connection_id)")
        .eq("id", draft_id)
        .eq("user_id", user.id)
        .single()
        .execute()
        .data
    )

    if draft["status"] not in ("rascunho", "aprovado", "erro"):
        raise AppError(f"Draft não pode ser publicado no status '{draft['status']}'")

    # Update status to publishing
    supabase.table("campaign_drafts").update(
        {"status": "publicando", "atualizado_em": datetime.now(timezone.utc).isoformat()}
    ).eq("id", draft_id).execute()

    act_id = draft["ad_accounts"]["act_id"]
    meta = await get_meta_client(act_id, user, supabase)

    try:
        payload = draft["payload"]
        result = await meta.create_campaign(
            name=payload["name"],
            objective=payload["objective"],
            special_ad_categories=payload.get("special_ad_categories", []),
            daily_budget_cents=payload.get("daily_budget_cents"),
            lifetime_budget_cents=payload.get("lifetime_budget_cents"),
        )

        # Success — update draft and create campaign
        meta_id = result["id"]
        supabase.table("campaign_drafts").update({
            "status": "criado",
            "meta_campaign_id": meta_id,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }).eq("id", draft_id).execute()

        acc = supabase.table("ad_accounts").select("id").eq("user_id", user.id).eq("act_id", act_id).single().execute().data
        supabase.table("campaigns").insert({
            "ad_account_id": acc["id"],
            "user_id": user.id,
            "meta_campaign_id": meta_id,
            "nome": payload["name"],
            "objetivo": payload["objective"],
            "status": "PAUSED",
            "verba_diaria": (payload.get("daily_budget_cents") or 0) / 100,
            "verba_total": (payload.get("lifetime_budget_cents") or 0) / 100,
        }).execute()

        updated = supabase.table("campaign_drafts").select("*").eq("id", draft_id).single().execute().data
        return DraftOut(
            id=updated["id"], status=updated["status"], payload=updated["payload"],
            meta_campaign_id=updated.get("meta_campaign_id"), erro_detalhes=updated.get("erro_detalhes"),
        )

    except Exception as exc:
        supabase.table("campaign_drafts").update({
            "status": "erro",
            "erro_detalhes": str(exc),
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }).eq("id", draft_id).execute()
        raise
    finally:
        await meta.close()


# === Activate / Pause ===


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    camp = (
        supabase.table("campaigns")
        .select("*, ad_accounts!inner(act_id)")
        .eq("id", campaign_id)
        .eq("user_id", user.id)
        .single()
        .execute()
        .data
    )

    if camp["status"] != "PAUSED":
        raise CampaignSafetyError()

    act_id = camp["ad_accounts"]["act_id"]
    meta = await get_meta_client(act_id, user, supabase)

    try:
        await meta.update_status(camp["meta_campaign_id"], "ACTIVE")
        supabase.table("campaigns").update({
            "status": "ACTIVE",
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }).eq("id", campaign_id).execute()
        return {"success": True, "status": "ACTIVE"}
    finally:
        await meta.close()


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    camp = (
        supabase.table("campaigns")
        .select("*, ad_accounts!inner(act_id)")
        .eq("id", campaign_id)
        .eq("user_id", user.id)
        .single()
        .execute()
        .data
    )

    act_id = camp["ad_accounts"]["act_id"]
    meta = await get_meta_client(act_id, user, supabase)

    try:
        await meta.update_status(camp["meta_campaign_id"], "PAUSED")
        supabase.table("campaigns").update({
            "status": "PAUSED",
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }).eq("id", campaign_id).execute()
        return {"success": True, "status": "PAUSED"}
    finally:
        await meta.close()
```

- [ ] **Step 3: Write integration test**

```python
# gestor-ads/backend/tests/integration/test_campaign_routers.py
from __future__ import annotations

from app.campaigns.schemas import DraftCreate, DraftOut, SyncRequest, SyncResponse


def test_sync_request_schema():
    req = SyncRequest(act_id="act_123")
    assert req.date_preset == "last_7d"


def test_sync_response_schema():
    resp = SyncResponse(campaigns_synced=5, metrics_upserted=35, errors=[{"campaign": "X", "error": "gone"}])
    assert resp.campaigns_synced == 5
    assert len(resp.errors) == 1


def test_draft_create_schema():
    draft = DraftCreate(act_id="act_123", payload={"name": "Test", "objective": "OUTCOME_LEADS"})
    assert draft.payload["objective"] == "OUTCOME_LEADS"


def test_draft_out_schema():
    out = DraftOut(id="d1", status="rascunho", payload={"name": "X"}, meta_campaign_id=None, erro_detalhes=None)
    assert out.status == "rascunho"
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/integration/test_campaign_routers.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add gestor-ads/backend/app/campaigns/
git add gestor-ads/backend/tests/integration/test_campaign_routers.py
git commit -m "feat(gestor-ads): campaign + account routers

- GET /accounts, /accounts/{act_id}
- GET /campaigns, /campaigns/{id}/insights
- POST /campaigns/sync (partial sync with error list)
- POST /campaigns/drafts, PATCH, POST .../publish
- POST /campaigns/{id}/activate, /campaigns/{id}/pause
- Drafts → campaigns flow with PAUSED creation
- 4 schema tests passing"
```

---

### Task 12: Analysis + Creatives + Audit Routers

**Files:**
- Create: `gestor-ads/backend/app/analysis/__init__.py`
- Create: `gestor-ads/backend/app/analysis/schemas.py`
- Create: `gestor-ads/backend/app/analysis/router.py`

**Interfaces:**
- Consumes: `evaluate()` (Task 6), `summarize_kpis()` (Task 7), `analyze_performance()` (Task 8), `get_current_user`, `get_supabase` (Task 10)
- Produces: Router at `/api` with endpoints: `POST /analysis/evaluate`, `POST /analysis/summary`, `POST /creatives/upload`, `GET /creatives`, `GET /audit-log`

- [ ] **Step 1: Write schemas**

```python
# gestor-ads/backend/app/analysis/schemas.py
from __future__ import annotations

from pydantic import BaseModel


class EvaluateRequest(BaseModel):
    act_id: str
    date_preset: str = "last_7d"


class RuleResultOut(BaseModel):
    severity: str
    rule_name: str
    action: str
    campaign: str
    reason: str
    should_pause: bool
    meta_entity_id: str | None


class EvaluateResponse(BaseModel):
    alerts: list[RuleResultOut]
    total: int


class SummaryRequest(BaseModel):
    act_id: str
    date_preset: str = "last_7d"
    nivel_tecnico: str = "avancado"


class SummaryResponse(BaseModel):
    resumo: str
    recomendacoes: list[str]
    acoes: list[dict]
    kpis: dict


class CreativeOut(BaseModel):
    id: str
    tipo: str
    storage_path: str
    meta_hash: str | None
    meta_video_id: str | None


class AuditLogOut(BaseModel):
    id: str
    acao: str
    entidade: str
    entidade_id: str | None
    criado_em: str
```

- [ ] **Step 2: Implement analysis router**

Create `gestor-ads/backend/app/analysis/__init__.py` (empty).

```python
# gestor-ads/backend/app/analysis/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile

from supabase import Client

from app.analysis.schemas import (
    AuditLogOut,
    CreativeOut,
    EvaluateRequest,
    EvaluateResponse,
    RuleResultOut,
    SummaryRequest,
    SummaryResponse,
)
from app.auth.models import User
from app.config import Settings, get_settings
from app.core.analysis import analyze_performance
from app.core.kpis import summarize_kpis
from app.core.rules import AccountThresholds, evaluate
from app.dependencies import get_current_user, get_supabase

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analysis/evaluate", response_model=EvaluateResponse)
async def run_evaluation(
    body: EvaluateRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    # Get account thresholds
    acc = (
        supabase.table("ad_accounts")
        .select("id, target_cpl, waste_limit, min_ctr, max_frequency")
        .eq("user_id", user.id)
        .eq("act_id", body.act_id)
        .single()
        .execute()
        .data
    )
    thresholds = AccountThresholds(
        target_cpl=acc.get("target_cpl") or 0,
        waste_limit=acc.get("waste_limit") or 100,
        min_ctr=acc.get("min_ctr") or 0.8,
        max_frequency=acc.get("max_frequency") or 3.0,
    )

    # Get metrics
    campaigns = (
        supabase.table("campaigns")
        .select("id, nome, meta_campaign_id")
        .eq("ad_account_id", acc["id"])
        .eq("user_id", user.id)
        .execute()
        .data
    )

    metrics: list[dict] = []
    for camp in campaigns:
        rows = (
            supabase.table("campaign_metrics")
            .select("*")
            .eq("campaign_id", camp["id"])
            .eq("user_id", user.id)
            .execute()
            .data
        )
        for r in rows:
            r["campaign"] = camp["nome"]
            r["meta_entity_id"] = camp["meta_campaign_id"]
            r["entity_level"] = "campaign"
            r["entity_name"] = camp["nome"]
        metrics.extend(rows)

    alerts = evaluate(metrics, thresholds)

    return EvaluateResponse(
        alerts=[
            RuleResultOut(
                severity=a.severity,
                rule_name=a.rule_name,
                action=a.action,
                campaign=a.campaign,
                reason=a.reason,
                should_pause=a.should_pause,
                meta_entity_id=a.meta_entity_id,
            )
            for a in alerts
        ],
        total=len(alerts),
    )


@router.post("/analysis/summary", response_model=SummaryResponse)
async def run_summary(
    body: SummaryRequest,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    # Get account thresholds
    acc = (
        supabase.table("ad_accounts")
        .select("id, target_cpl, waste_limit, min_ctr, max_frequency")
        .eq("user_id", user.id)
        .eq("act_id", body.act_id)
        .single()
        .execute()
        .data
    )
    thresholds = AccountThresholds(
        target_cpl=acc.get("target_cpl") or 0,
        waste_limit=acc.get("waste_limit") or 100,
        min_ctr=acc.get("min_ctr") or 0.8,
        max_frequency=acc.get("max_frequency") or 3.0,
    )

    # Get metrics
    campaigns = (
        supabase.table("campaigns")
        .select("id, nome, meta_campaign_id")
        .eq("ad_account_id", acc["id"])
        .eq("user_id", user.id)
        .execute()
        .data
    )

    metrics: list[dict] = []
    for camp in campaigns:
        rows = (
            supabase.table("campaign_metrics")
            .select("*")
            .eq("campaign_id", camp["id"])
            .eq("user_id", user.id)
            .execute()
            .data
        )
        for r in rows:
            r["campaign"] = camp["nome"]
            r["meta_entity_id"] = camp["meta_campaign_id"]
            r["entity_level"] = "campaign"
            r["entity_name"] = camp["nome"]
        metrics.extend(rows)

    result = await analyze_performance(
        metrics=metrics,
        thresholds=thresholds,
        nivel_tecnico=body.nivel_tecnico,
        anthropic_api_key=settings.anthropic_api_key,
    )

    kpis = summarize_kpis(metrics)

    return SummaryResponse(
        resumo=result.resumo,
        recomendacoes=result.recomendacoes,
        acoes=result.acoes,
        kpis={
            "total_spend": kpis.total_spend,
            "total_leads": kpis.total_leads,
            "cpl_medio": kpis.cpl_medio,
            "ctr_medio": kpis.ctr_medio,
            "tendencia": kpis.tendencia,
            "melhor_campanha": kpis.melhor_campanha,
            "pior_campanha": kpis.pior_campanha,
        },
    )


# === Creatives ===


@router.post("/creatives/upload", response_model=CreativeOut)
async def upload_creative(
    act_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    acc = (
        supabase.table("ad_accounts")
        .select("id")
        .eq("user_id", user.id)
        .eq("act_id", act_id)
        .single()
        .execute()
        .data
    )

    content_type = file.content_type or ""
    tipo = "video" if "video" in content_type else "image"
    file_bytes = await file.read()

    # Upload to Supabase Storage
    storage_path = f"{user.id}/{acc['id']}/{file.filename}"
    supabase.storage.from_("creatives").upload(storage_path, file_bytes)

    row = (
        supabase.table("creatives")
        .insert({
            "user_id": user.id,
            "ad_account_id": acc["id"],
            "tipo": tipo,
            "storage_path": storage_path,
        })
        .execute()
        .data[0]
    )

    return CreativeOut(
        id=row["id"],
        tipo=row["tipo"],
        storage_path=row["storage_path"],
        meta_hash=row.get("meta_hash"),
        meta_video_id=row.get("meta_video_id"),
    )


@router.get("/creatives", response_model=list[CreativeOut])
async def list_creatives(
    act_id: str | None = None,
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    query = supabase.table("creatives").select("*").eq("user_id", user.id)
    if act_id:
        acc = supabase.table("ad_accounts").select("id").eq("user_id", user.id).eq("act_id", act_id).single().execute().data
        query = query.eq("ad_account_id", acc["id"])
    rows = query.execute().data
    return [
        CreativeOut(
            id=r["id"], tipo=r["tipo"], storage_path=r["storage_path"],
            meta_hash=r.get("meta_hash"), meta_video_id=r.get("meta_video_id"),
        )
        for r in rows
    ]


# === Audit Log ===


@router.get("/audit-log", response_model=list[AuditLogOut])
async def list_audit_log(
    entidade: str | None = None,
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    query = (
        supabase.table("audit_log")
        .select("id, acao, entidade, entidade_id, criado_em")
        .eq("user_id", user.id)
        .order("criado_em", desc=True)
        .limit(limit)
    )
    if entidade:
        query = query.eq("entidade", entidade)
    rows = query.execute().data
    return rows
```

- [ ] **Step 3: Run ruff check**

```bash
ruff check app/ tests/
```

Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add gestor-ads/backend/app/analysis/
git commit -m "feat(gestor-ads): analysis, creatives, and audit routers

- POST /analysis/evaluate — runs rules engine, returns alerts
- POST /analysis/summary — AI analysis + KPIs + recommendations
- POST /creatives/upload — Supabase Storage upload
- GET /creatives — list user's creatives
- GET /audit-log — paginated audit history"
```

---

### Task 13: App Assembly + Dockerfile + CI

**Files:**
- Create: `gestor-ads/backend/app/main.py`
- Create: `gestor-ads/backend/Dockerfile`
- Create: `gestor-ads/backend/.env.example`
- Create: `gestor-ads/.github/workflows/ci.yml`

**Interfaces:**
- Consumes: all routers (Tasks 10, 11, 12), exception hierarchy (Task 1), `Settings` (Task 1)
- Produces: runnable FastAPI app at `app.main:app`, Dockerfile, CI workflow

- [ ] **Step 1: Implement main.py**

```python
# gestor-ads/backend/app/main.py
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analysis.router import router as analysis_router
from app.auth.router import router as auth_router
from app.campaigns.router import router as campaigns_router
from app.config import get_settings
from app.shared.exceptions import AppError

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="Gestor Ads API",
    description="Backend unificado — Campaign Optimizer + Gestor de Tráfego",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "meta": exc.meta,
        },
    )


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Mount routers
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(analysis_router)
```

- [ ] **Step 2: Create .env.example**

```env
# gestor-ads/backend/.env.example

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...

# Meta OAuth
META_APP_ID=123456
META_APP_SECRET=abc...
META_REDIRECT_URI=https://ads.creativeagenciamkt.com.br/api/auth/meta/callback

# Security
FERNET_KEY=base64-encoded-32-byte-key
JWT_SECRET=random-secret-for-state-jwt

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# App
ENVIRONMENT=development
LOG_LEVEL=info
CORS_ORIGINS=["http://localhost:3000"]
```

- [ ] **Step 3: Create Dockerfile**

```dockerfile
# gestor-ads/backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create CI workflow**

```yaml
# gestor-ads/.github/workflows/ci.yml
name: Gestor Ads CI

on:
  push:
    branches: [main]
    paths: ['gestor-ads/**']
  pull_request:
    paths: ['gestor-ads/**']

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: gestor-ads/backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint
        run: |
          ruff check app/ tests/
          ruff format --check app/ tests/

      - name: Test
        env:
          FERNET_KEY: VGVzdEtleUZvclRlc3Rpbmc9PT09PT09PT09PT09PQ==
          JWT_SECRET: ci-test-secret
          ENVIRONMENT: test
        run: pytest tests/unit/ -v --tb=short
```

- [ ] **Step 5: Test that the app starts locally**

```bash
cd gestor-ads/backend
pip install -e ".[dev]"
python -c "from app.main import app; print('App loaded:', app.title)"
```

Expected: `App loaded: Gestor Ads API`

- [ ] **Step 6: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests pass (unit + integration schema tests)

- [ ] **Step 7: Run ruff on everything**

```bash
ruff check app/ tests/
ruff format --check app/ tests/
```

Expected: no errors

- [ ] **Step 8: Commit**

```bash
git add gestor-ads/backend/app/main.py gestor-ads/backend/Dockerfile
git add gestor-ads/backend/.env.example gestor-ads/.github/
git commit -m "feat(gestor-ads): app assembly, Dockerfile, and CI

- FastAPI app with CORS, exception handler, health check
- All routers mounted: auth, campaigns, analysis
- Dockerfile for production deploy
- GitHub Actions: ruff + pytest on push/PR
- Deploy target: ads.creativeagenciamkt.com.br"
```

---

## Post-Implementation Checklist

After all 13 tasks are done:

1. **Apply Supabase migration** (Task 9) if not yet applied
2. **Configure DNS**: `ads.creativeagenciamkt.com.br` CNAME → deploy provider
3. **Set environment variables** on Railway/Render using `.env.example` as reference
4. **Create Meta App** on Meta for Developers with required permissions
5. **Generate Fernet key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
6. **First deploy**: push to main → CI runs → auto-deploy
7. **Test OAuth flow**: `GET /api/auth/meta/login` → authorize → callback → accounts listed
8. **Test sync**: `POST /api/campaigns/sync` with a real ad account
