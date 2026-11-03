from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Prevent real env vars from leaking into tests."""
    monkeypatch.setenv("FERNET_KEY", "VGVzdEtleUZvclRlc3Rpbmc9PT09PT09PT09PT09PQ==")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-unit-tests")


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
