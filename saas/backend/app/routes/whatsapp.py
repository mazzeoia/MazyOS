from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from postgrest.exceptions import APIError

from ..auth import CurrentUser, get_current_user
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/status")
def whatsapp_status(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, object]:
    admin = get_supabase_admin()
    meta_connection = (
        admin.table("meta_connections")
        .select("id,created_at")
        .eq("owner_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    try:
        clients = (
            admin.table("clients")
            .select(
                "id,name,whatsapp_number,whatsapp_connected,whatsapp_connection_mode,"
                "whatsapp_phone_number_id,whatsapp_business_account_id,whatsapp_real_numbers,whatsapp_notes,meta_ad_account_id"
            )
            .eq("owner_id", user.id)
            .execute()
        )
    except APIError as exc:
        if "whatsapp_" not in str(exc):
            raise
        return {
            "ok": True,
            "schemaReady": False,
            "connected": False,
            "source": "client_settings",
            "businessAccounts": [],
            "phoneNumbers": [],
            "pages": [],
            "linkedClients": [],
            "message": "Campos de WhatsApp ainda nao existem no Supabase. Aplique a migracao para habilitar a configuracao por cliente.",
        }
    connected_clients = [client for client in (clients.data or []) if client.get("whatsapp_connected") or client.get("whatsapp_number")]
    return {
        "ok": True,
        "schemaReady": True,
        "connected": bool(meta_connection.data) and bool(connected_clients),
        "source": "client_settings",
        "businessAccounts": [],
        "phoneNumbers": [
            {
                "client_id": client.get("id"),
                "client_name": client.get("name"),
                "display_phone_number": client.get("whatsapp_number") or "",
                "verified_name": client.get("name") or "",
                "quality_rating": "API" if client.get("whatsapp_connection_mode") == "official_api" else "MANUAL",
                "code_verification_status": "CONNECTED" if client.get("whatsapp_connected") else "PENDING",
                "connection_mode": client.get("whatsapp_connection_mode") or "manual",
                "phone_number_id": client.get("whatsapp_phone_number_id") or "",
                "waba_id": client.get("whatsapp_business_account_id") or "",
            }
            for client in connected_clients
        ],
        "pages": [],
        "linkedClients": connected_clients,
        "message": "WhatsApp pode ser configurado por cliente sem API oficial ou preparado com IDs da Cloud API oficial.",
    }


@router.post("/refresh")
def refresh_whatsapp_assets(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, object]:
    status = whatsapp_status(user)
    return {
        "ok": True,
        "cached": True,
        "businessAccountsSynced": 0,
        "phoneNumbersSynced": len(status.get("phoneNumbers", [])),
        "businessAccounts": [],
        "phoneNumbers": status.get("phoneNumbers", []),
        "message": "WhatsApp configurado por cliente. Ajuste o modo manual/API oficial e os numeros reais em Configuracoes.",
    }
