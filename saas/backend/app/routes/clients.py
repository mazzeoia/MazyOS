from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from postgrest.exceptions import APIError

from ..auth import CurrentUser, get_current_user
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/clients", tags=["clients"])


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    source: str = "manual"
    meta_ad_account_id: str | None = None
    google_ads_customer_id: str | None = None
    meta_page_id: str | None = None
    meta_instagram_account_id: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    monthly_budget: float | None = Field(default=None, ge=0)
    target_cpl: float | None = Field(default=None, ge=0)
    account_manager: str | None = Field(default=None, max_length=120)
    business_goal: str | None = Field(default=None, max_length=240)
    qualified_lead_definition: str | None = Field(default=None, max_length=600)
    whatsapp_number: str | None = Field(default=None, max_length=40)
    whatsapp_connected: bool | None = None
    whatsapp_connection_mode: str | None = Field(default=None, max_length=20)
    whatsapp_phone_number_id: str | None = Field(default=None, max_length=80)
    whatsapp_business_account_id: str | None = Field(default=None, max_length=80)
    whatsapp_real_numbers: int | None = Field(default=None, ge=0)
    whatsapp_notes: str | None = Field(default=None, max_length=600)


def _default_slug(user: CurrentUser) -> str:
    prefix = (user.email or "creative").split("@", 1)[0]
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in prefix).strip("-")
    return f"{cleaned or 'creative'}-{user.id[:8]}"


def _get_or_create_organization_id(client, user: CurrentUser) -> str:
    existing = (
        client.table("organizations")
        .select("id")
        .eq("owner_user_id", user.id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    name = "Creative"
    if user.email:
        name = user.email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()

    created = (
        client.table("organizations")
        .insert({"name": name, "slug": _default_slug(user), "owner_user_id": user.id})
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Nao foi possivel criar organizacao.")
    return created.data[0]["id"]


def _normalize_meta_account_id(value: str | None) -> str:
    return (value or "").removeprefix("act_").strip()


def _canonical_meta_account_id(value: str | None) -> str | None:
    normalized = _normalize_meta_account_id(value)
    if not normalized:
        return None
    return f"act_{normalized}" if normalized.isdigit() else value


def _normalize_google_customer_id(value: str | None) -> str:
    return "".join(char for char in (value or "") if char.isdigit())


@router.get("")
def list_clients(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, object]:
    client = get_supabase_admin()
    result = (
        client.table("clients")
        .select("*")
        .eq("owner_id", user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"ok": True, "clients": result.data or []}


@router.post("")
def create_client(
    payload: ClientCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, object]:
    client = get_supabase_admin()
    organization_id = _get_or_create_organization_id(client, user)

    meta_ad_account_id = _canonical_meta_account_id(payload.meta_ad_account_id)
    google_ads_customer_id = _normalize_google_customer_id(payload.google_ads_customer_id)

    if meta_ad_account_id:
        normalized_payload_account = _normalize_meta_account_id(meta_ad_account_id)
        existing = (
            client.table("clients")
            .select("*")
            .eq("owner_id", user.id)
            .execute()
        )
        for existing_client in existing.data or []:
            if _normalize_meta_account_id(existing_client.get("meta_ad_account_id")) == normalized_payload_account:
                return {"ok": True, "client": existing_client, "alreadyExists": True}
    if google_ads_customer_id:
        existing = (
            client.table("clients")
            .select("*")
            .eq("owner_id", user.id)
            .execute()
        )
        for existing_client in existing.data or []:
            if _normalize_google_customer_id(existing_client.get("google_ads_customer_id")) == google_ads_customer_id:
                return {"ok": True, "client": existing_client, "alreadyExists": True}

    row = {
        "organization_id": organization_id,
        "owner_id": user.id,
        "name": payload.name,
        "source": payload.source,
        "meta_ad_account_id": meta_ad_account_id,
        "google_ads_customer_id": google_ads_customer_id or None,
        "meta_page_id": payload.meta_page_id,
        "meta_instagram_account_id": payload.meta_instagram_account_id,
    }
    try:
        result = client.table("clients").insert(row).execute()
    except APIError as exc:
        raise HTTPException(status_code=500, detail=exc.message) from exc
    if not result.data:
        raise HTTPException(status_code=500, detail="Nao foi possivel criar cliente.")
    return {"ok": True, "client": result.data[0]}


@router.patch("/{client_id}")
def update_client(
    client_id: str,
    payload: ClientUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, object]:
    client = get_supabase_admin()
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhuma alteracao enviada.")
    if "whatsapp_connection_mode" in data:
        mode = data.get("whatsapp_connection_mode") or "manual"
        if mode not in {"manual", "official_api"}:
            raise HTTPException(status_code=400, detail="Modo de WhatsApp invalido.")
        data["whatsapp_connection_mode"] = mode

    data["updated_at"] = datetime.now(UTC).isoformat()
    try:
        result = (
            client.table("clients")
            .update(data)
            .eq("id", client_id)
            .eq("owner_id", user.id)
            .execute()
        )
    except APIError as exc:
        if "does not exist" in exc.message:
            raise HTTPException(
                status_code=500,
                detail="Colunas de configuracao do cliente nao existem. Aplique saas/supabase/schema.sql no Supabase.",
            ) from exc
        raise HTTPException(status_code=500, detail=exc.message) from exc
    if not result.data:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    return {"ok": True, "client": result.data[0]}
