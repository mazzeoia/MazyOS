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
    """MetaRateLimitError -> MetaAPIError -> AppError -> Exception."""
    err = MetaRateLimitError("test")
    assert isinstance(err, MetaAPIError)
    assert isinstance(err, AppError)
    assert isinstance(err, Exception)
