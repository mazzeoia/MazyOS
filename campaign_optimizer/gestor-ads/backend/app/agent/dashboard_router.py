# app/agent/dashboard_router.py
"""Dashboard-facing side of the agent feature.

This is deliberately a *separate* router from app/agent/router.py (which holds
the Telegram/Evolution webhook endpoints and is mounted standalone in
app/agent/main.py for the chat bot deployment). The dashboard frontend talks
to the main backend (app/main.py), authenticating with the same Supabase JWT
used by every other protected route there (see app/dependencies.py::get_current_user).
Mounting webhook endpoints into the dashboard-facing app (or vice versa) would
mix two different trust boundaries — public, secret-header-authenticated
webhooks vs. JWT-authenticated dashboard calls — so this small router keeps
the dashboard-only endpoint in its own module, mounted from app/main.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import Client

from app.agent.conversation import link_conversation_by_code
from app.agent.router import _adapter_for
from app.auth.models import User
from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_supabase
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/agent", tags=["agent"])


class LinkChatRequest(BaseModel):
    code: str


class LinkChatResponse(BaseModel):
    success: bool
    message: str
    conversation_id: str
    channel: str


@router.post("/link-chat", response_model=LinkChatResponse)
async def link_chat(
    body: LinkChatRequest,
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    supabase: Client = Depends(get_supabase),
) -> LinkChatResponse:
    """Called from the dashboard's "Conectar WhatsApp/Telegram" screen after the
    user types in the code the chat sent them. Binds conversations.owner_id to
    the logged-in dashboard user and notifies the chat that it's connected.
    """
    conv = await link_conversation_by_code(supabase, body.code, user.id)
    if not conv:
        raise NotFoundError("Código inválido ou expirado. Peça um novo código pelo chat.")

    has_meta = bool(
        supabase.table("meta_connections").select("id").eq("owner_id", user.id).execute().data
    )
    if has_meta:
        texto = "Conta conectada! Pode mandar sua mensagem que eu já cuido dos seus anúncios."
    else:
        texto = (
            "Conta conectada! Agora conecte sua conta Meta no painel pra eu conseguir "
            "mexer nos seus anúncios."
        )

    adapter = _adapter_for(conv["channel"], settings)
    await adapter.send_text(conv["channel_user_id"], texto)

    return LinkChatResponse(
        success=True,
        message="Conversa vinculada com sucesso",
        conversation_id=conv["id"],
        channel=conv["channel"],
    )
