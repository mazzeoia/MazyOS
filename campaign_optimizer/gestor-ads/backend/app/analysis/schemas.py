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


class AnalysisHistoryOut(BaseModel):
    id: str
    nivel_tecnico: str
    resumo: str
    recomendacoes: list[str]
    acoes: list[dict]
    kpis: dict
    criado_em: str
