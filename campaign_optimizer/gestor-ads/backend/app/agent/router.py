# app/agent/router.py
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from supabase import Client

from app.agent.channels.base import IncomingMessage
from app.agent.channels.evolution import EvolutionAdapter
from app.agent.channels.telegram import TelegramAdapter
from app.agent.conversation import (
    generate_link_code,
    get_or_create_conversation,
    get_recent_messages,
    message_already_processed,
    record_message,
)
from app.agent.llm import run_agent_turn
from app.agent.tools import ToolContext
from app.agent.transcription import transcribe_audio
from app.config import Settings, get_settings
from app.dependencies import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

HISTORY_LIMIT = 10

# Chat users are NEVER auto-provisioned: they must already have a dashboard
# account. Linking happens via a short one-time code: we generate it here and
# the user enters it on the dashboard's "Conectar WhatsApp/Telegram" screen,
# which calls POST /agent/link-chat (see app/agent/dashboard_router.py) to
# bind conversations.owner_id. Connecting Meta afterwards reuses the existing
# OAuth flow (app/auth/router.py::meta_callback already notifies the chat).
_ONBOARDING_TEMPLATE = (
    "Oi! Pra eu cuidar dos seus anúncios por aqui, acesse o painel em {url}, entre na sua "
    "conta e digite esse código pra conectar essa conversa: {code} (válido por 15 min)."
)
_EVOLUTION_DISCLAIMER = (
    "\n\nObs: esse canal de WhatsApp é experimental (conexão não oficial) e "
    "tem algum risco de o número ser bloqueado pelo WhatsApp."
)


def _adapter_for(channel: str, settings: Settings):
    if channel == "telegram":
        return TelegramAdapter(bot_token=settings.telegram_bot_token)
    return EvolutionAdapter(
        base_url=settings.evolution_base_url,
        api_key=settings.evolution_api_key,
        instance=settings.evolution_instance,
    )


def _external_message_id(msg: IncomingMessage) -> str | None:
    """Channel's own message id, used for webhook idempotency."""
    if msg.channel == "telegram":
        mid = msg.raw.get("message", {}).get("message_id")
        return str(mid) if mid is not None else None
    mid = msg.raw.get("data", {}).get("key", {}).get("id")
    return str(mid) if mid else None


async def process_incoming_message(msg: IncomingMessage, settings: Settings, supabase: Client) -> None:
    """Runs off the request/response cycle — this is what BackgroundTasks calls."""
    adapter = _adapter_for(msg.channel, settings)
    conv = await get_or_create_conversation(supabase, msg.channel, msg.channel_user_id)

    external_id = _external_message_id(msg)
    if external_id and await message_already_processed(supabase, conv["id"], external_id):
        logger.info("Skipping duplicate webhook delivery %s", external_id)
        return

    if not conv.get("owner_id"):
        # Not linked to a dashboard account yet. The chat never creates users;
        # onboarding is: log in on the dashboard and enter the one-time code
        # we send here to link this conversation (POST /agent/link-chat).
        code = await generate_link_code(supabase, conv["id"])
        texto_onboarding = _ONBOARDING_TEMPLATE.format(url=settings.frontend_url, code=code)
        if msg.channel == "evolution":
            texto_onboarding += _EVOLUTION_DISCLAIMER
        await adapter.send_text(msg.channel_user_id, texto_onboarding)
        return

    texto = msg.text or ""
    if msg.audio_ref:
        # Media download happens HERE, in the background task — never inside
        # the webhook handler, which must ack immediately.
        try:
            audio_bytes = await adapter.download_media(msg.audio_ref)
            texto = await transcribe_audio(audio_bytes, settings.openai_api_key)
        except Exception:
            logger.warning("Audio transcription failed", exc_info=True)
            await adapter.send_text(msg.channel_user_id, "Não consegui entender o áudio, pode repetir em texto?")
            return

    await record_message(supabase, conv["id"], "user", texto, external_message_id=external_id)

    profile = (
        supabase.table("profiles").select("nivel_tecnico").eq("id", conv["owner_id"]).execute().data
    )
    nivel_tecnico = profile[0]["nivel_tecnico"] if profile else "avancado"

    ctx = ToolContext(
        supabase=supabase,
        settings=settings,
        user_id=conv["owner_id"],
        conversation_id=conv["id"],
        ad_account_id=conv.get("ad_account_id"),
    )

    meta_client = None
    if conv.get("ad_account_id"):
        from app.auth.models import User
        from app.dependencies import build_meta_client

        acc = supabase.table("ad_accounts").select("external_id").eq("id", conv["ad_account_id"]).single().execute().data
        meta_client = await build_meta_client(acc["external_id"], User(id=conv["owner_id"], email=""), supabase, settings)

    historico = await get_recent_messages(supabase, conv["id"], limit=HISTORY_LIMIT)
    # The message just recorded is passed as `mensagem_atual` — don't repeat it.
    if historico and historico[-1] == {"role": "user", "content": texto}:
        historico = historico[:-1]

    result = await run_agent_turn(
        ctx=ctx,
        meta_client=meta_client,
        resumo_memoria=conv.get("resumo_memoria", ""),
        memoria_negocio=conv.get("memoria_negocio", {}),
        historico=historico,
        mensagem_atual=texto,
        nivel_tecnico=nivel_tecnico,
        anthropic_api_key=settings.anthropic_api_key,
        anthropic_workspace_id=settings.anthropic_workspace_id,
    )

    await record_message(
        supabase, conv["id"], "assistant", result["resposta"],
        modelo_usado=result["modelo_usado"], tokens_input=result["tokens_input"], tokens_output=result["tokens_output"],
    )
    await adapter.send_text(msg.channel_user_id, result["resposta"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    supabase: Client = Depends(get_supabase),
):
    # Telegram echoes the secret registered via setWebhook(secret_token=...).
    # Fails open when unset so dev setups work — production MUST set
    # TELEGRAM_WEBHOOK_SECRET, otherwise anyone can post fake updates.
    if settings.telegram_webhook_secret and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    adapter = TelegramAdapter(bot_token=settings.telegram_bot_token)
    msg = await adapter.receive_webhook(payload)
    background_tasks.add_task(process_incoming_message, msg, settings, supabase)
    return {"ok": True}


@router.post("/evolution/webhook")
async def evolution_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    apikey: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    supabase: Client = Depends(get_supabase),
):
    # Evolution sends the instance apikey back on its webhooks. Fails open
    # when unset (dev only) — production MUST set EVOLUTION_API_KEY.
    if settings.evolution_api_key and apikey != settings.evolution_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    adapter = EvolutionAdapter(
        base_url=settings.evolution_base_url, api_key=settings.evolution_api_key, instance=settings.evolution_instance
    )
    msg = await adapter.receive_webhook(payload)
    background_tasks.add_task(process_incoming_message, msg, settings, supabase)
    return {"ok": True}
