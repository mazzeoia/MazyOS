from __future__ import annotations

from pydantic import BaseModel


class AutomationSettingsOut(BaseModel):
    auto_pause_enabled: bool
    server_schedule_enabled: bool
    notify_email: bool
    notify_whatsapp: bool


class AutomationSettingsUpdate(BaseModel):
    act_id: str
    auto_pause_enabled: bool = False
    server_schedule_enabled: bool = False
    notify_email: bool = True


class AutomationRunRequest(BaseModel):
    act_id: str
    date_preset: str = "last_7d"


class AutomationRunOut(BaseModel):
    alerts_found: int
    paused_count: int
    errors: list[str]


class AutomationRunAllOut(BaseModel):
    accounts_checked: int
    total_alerts: int
    total_paused: int
    errors: list[str]


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    severity: str
    lida: bool
    criado_em: str
