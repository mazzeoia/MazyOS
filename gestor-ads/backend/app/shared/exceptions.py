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
