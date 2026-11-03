from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Form, Query
from fastapi.responses import RedirectResponse
from supabase import Client

from app.auth.meta_oauth import generate_oauth_url, validate_state
from app.auth.models import (
    AuthResponse,
    LoginRequest,
    MetaOAuthURL,
    RegisterRequest,
    User,
)
from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_supabase, get_token_manager
from app.meta.token_manager import TokenManager
from app.shared.crypto import parse_meta_signed_request
from app.shared.exceptions import AppError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


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
        result = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return AuthResponse(
            access_token=result.session.access_token,
            user_id=str(result.user.id),
            email=result.user.email or body.email,
        )
    except Exception as exc:
        raise AppError("Email ou senha incorretos", meta={"detail": str(exc)})


@router.get("/meta/login", response_model=MetaOAuthURL)
async def meta_login(
    conversation_id: str | None = Query(default=None),
    user: User = Depends(get_current_user),
):
    # conversation_id lets the dashboard flow (e.g. right after linking a chat
    # via /agent/link-chat) tell the OAuth callback which chat to notify once
    # Meta is connected — see meta_callback below.
    url = generate_oauth_url(user.id, conversation_id)
    return MetaOAuthURL(url=url)


@router.get("/meta/callback")
async def meta_callback(
    code: str = Query(...),
    state: str = Query(...),
    supabase: Client = Depends(get_supabase),
    tm: TokenManager = Depends(get_token_manager),
    settings: Settings = Depends(get_settings),
):
    # Validate state token
    try:
        user_id, conversation_id = validate_state(state)
    except ValueError as exc:
        raise AppError(str(exc))

    # Exchange code for long-lived token
    pair = await tm.exchange_code(code)
    encrypted = tm.encrypt(pair.access_token)

    # Get Meta user info
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://graph.facebook.com/v23.0/me",
            params={"access_token": pair.access_token, "fields": "id,name"},
        )
        meta_user = resp.json()

    # Save connection — schema uses owner_id + access_token + expires_at
    supabase.table("meta_connections").upsert(
        {
            "owner_id": user_id,
            "meta_user_id": meta_user["id"],
            "meta_user_name": meta_user.get("name", ""),
            "access_token": encrypted,
            "expires_at": pair.expires_at.isoformat(),
            "scopes": ["ads_management", "ads_read", "business_management", "pages_show_list"],
        },
        on_conflict="owner_id,meta_user_id",
    ).execute()

    # List ad accounts from Facebook
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://graph.facebook.com/v23.0/me/adaccounts",
            params={
                "access_token": pair.access_token,
                "fields": "id,name,account_status,currency,timezone_name,business",
            },
        )
        accounts_data = resp.json().get("data", [])

    # Upsert each ad account into ad_accounts table
    for acc in accounts_data:
        try:
            supabase.table("ad_accounts").upsert(
                {
                    "client_id": user_id,
                    "external_id": acc["id"],
                    "name": acc.get("name", ""),
                    "currency": acc.get("currency", "BRL"),
                    "timezone": acc.get("timezone_name", "America/Sao_Paulo"),
                    "status": "active",
                    "platform": "meta_ads",
                },
                on_conflict="client_id,platform,external_id",
            ).execute()
        except Exception as exc:
            logger.warning("Erro ao salvar ad account %s: %s", acc["id"], exc)

    logger.info("Meta callback: %d ad accounts salvas para user %s", len(accounts_data), user_id)

    if conversation_id:
        from app.agent.channels.evolution import EvolutionAdapter
        from app.agent.channels.telegram import TelegramAdapter

        conv_rows = supabase.table("conversations").select("*").eq("id", conversation_id).execute().data
        if conv_rows:
            conv = conv_rows[0]
            supabase.table("conversations").update({"owner_id": user_id}).eq("id", conversation_id).execute()
            adapter = (
                TelegramAdapter(bot_token=settings.telegram_bot_token)
                if conv["channel"] == "telegram"
                else EvolutionAdapter(
                    base_url=settings.evolution_base_url,
                    api_key=settings.evolution_api_key,
                    instance=settings.evolution_instance,
                )
            )
            lines = [f"{i + 1}. {a.get('name', '')} ({a['id']})" for i, a in enumerate(accounts_data)]
            text = "Conectei sua conta Meta! Encontrei essas contas de anúncio:\n" + "\n".join(lines)
            text += "\n\nResponda com o número ou nome da conta que você quer usar."
            await adapter.send_text(conv["channel_user_id"], text)

    # Redirect user back to frontend dashboard
    return RedirectResponse(url="https://ads.creativeagenciamkt.com.br/", status_code=302)


@router.post("/meta/deauthorize")
async def meta_deauthorize(
    signed_request: str = Form(...),
    supabase: Client = Depends(get_supabase),
):
    """Meta calls this when a user removes/deauthorizes the app on their Facebook
    account. We revoke the stored token, disconnect the ad accounts and turn off
    automation for that owner, so nothing keeps trying to act on their behalf.
    """
    settings = get_settings()

    try:
        data = parse_meta_signed_request(signed_request, settings.meta_app_secret)
    except ValueError as exc:
        logger.warning("Deauthorize: signed_request inválido: %s", exc)
        return {"status": "ignored"}

    meta_user_id = data.get("user_id")
    if not meta_user_id:
        logger.warning("Deauthorize: signed_request sem user_id: %s", data)
        return {"status": "ignored"}

    connections = (
        supabase.table("meta_connections")
        .select("id, owner_id")
        .eq("meta_user_id", meta_user_id)
        .execute()
        .data
    )
    if not connections:
        logger.info("Deauthorize: nenhuma conexão encontrada para meta_user_id=%s", meta_user_id)
        return {"status": "ok"}

    now = datetime.now(timezone.utc).isoformat()

    for conn in connections:
        owner_id = conn["owner_id"]

        # Invalidate the stored token — clearing it (instead of deleting the row)
        # keeps history but makes it unusable immediately.
        supabase.table("meta_connections").update(
            {"access_token": "", "expires_at": now}
        ).eq("id", conn["id"]).execute()

        # Mark this owner's Meta ad accounts as disconnected.
        supabase.table("ad_accounts").update({"status": "disconnected"}).eq(
            "client_id", owner_id
        ).eq("platform", "meta_ads").execute()

        # Turn off automation so nothing tries to auto-pause a campaign we can no
        # longer reach.
        supabase.table("automation_settings").update(
            {"auto_pause_enabled": False, "server_schedule_enabled": False}
        ).eq("owner_id", owner_id).execute()

        supabase.table("audit_log").insert(
            {
                "owner_id": owner_id,
                "acao": "meta_deauthorize",
                "entidade": "meta_connections",
                "request": {"meta_user_id": meta_user_id},
                "response": {"status": "revoked"},
                "origem": "meta_webhook",
            }
        ).execute()

        logger.info(
            "Deauthorize processado: owner_id=%s meta_user_id=%s", owner_id, meta_user_id
        )

    return {"status": "ok"}
