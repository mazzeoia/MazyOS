from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from postgrest.exceptions import APIError

from ..auth import CurrentUser, get_current_user
from ..config import Settings, get_settings
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/google-ads", tags=["google-ads"])


def _redirect_uri(settings: Settings) -> str:
    return f"{settings.app_url.rstrip('/')}/api/google-ads/oauth/callback"


def _sign_state(payload: dict[str, Any], secret: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _read_state(state: str, secret: str) -> dict[str, Any]:
    try:
        body, signature = state.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="State invalido.") from exc

    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="State invalido.")

    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=400, detail="State expirado.")
    return payload


def _missing_google_settings(settings: Settings) -> list[str]:
    return [
        name
        for name, value in {
            "GOOGLE_ADS_CLIENT_ID": settings.google_ads_client_id,
            "GOOGLE_ADS_CLIENT_SECRET": settings.google_ads_client_secret,
            "GOOGLE_ADS_DEVELOPER_TOKEN": settings.google_ads_developer_token,
            "SUPABASE_SECRET_KEY": settings.supabase_secret_key,
        }.items()
        if not value
    ]


def _google_ads_base_url(settings: Settings) -> str:
    return f"https://googleads.googleapis.com/{settings.google_ads_api_version}"


def _require_google_settings(settings: Settings) -> None:
    missing = _missing_google_settings(settings)
    if missing:
        raise HTTPException(status_code=500, detail=f"Configure: {', '.join(missing)}.")


def _period_bounds(period: str, since: str | None = None, until: str | None = None) -> tuple[str, str]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    if period == "today":
        return today.isoformat(), today.isoformat()
    if period == "yesterday":
        return yesterday.isoformat(), yesterday.isoformat()
    if period == "last_7d":
        return (yesterday - timedelta(days=6)).isoformat(), yesterday.isoformat()
    if period == "custom":
        if not since or not until:
            raise HTTPException(status_code=400, detail="Informe data inicial e final.")
        return since, until
    return (yesterday - timedelta(days=29)).isoformat(), yesterday.isoformat()


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _clean_customer_id(value: str | None) -> str:
    return "".join(char for char in (value or "") if char.isdigit())


def _error_message(detail: Any) -> str:
    if isinstance(detail, dict):
        error = detail.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(detail.get("message") or detail)
    return str(detail)


def _google_headers(settings: Settings, access_token: str, login_customer_id: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": settings.google_ads_developer_token,
        "Content-Type": "application/json",
    }
    login_customer = _clean_customer_id(login_customer_id or settings.google_ads_login_customer_id)
    if login_customer:
        headers["login-customer-id"] = login_customer
    return headers


async def _refresh_access_token(refresh_token: str, settings: Settings) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=_error_message(response.json()))
    return response.json()


async def _latest_connection(admin, user_id: str, settings: Settings) -> dict[str, Any]:
    connection = (
        admin.table("google_ads_connections")
        .select("*")
        .eq("owner_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not connection.data:
        raise HTTPException(status_code=400, detail="Conecte o Google Ads antes de sincronizar.")
    row = connection.data[0]
    refresh_token = row.get("refresh_token")
    expires_at = row.get("expires_at")
    should_refresh = bool(refresh_token)
    if expires_at:
        try:
            should_refresh = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00")) <= datetime.now(UTC) + timedelta(minutes=2)
        except ValueError:
            should_refresh = bool(refresh_token)
    if should_refresh and refresh_token:
        token_data = await _refresh_access_token(refresh_token, settings)
        row["access_token"] = token_data["access_token"]
        row["expires_at"] = (datetime.now(UTC) + timedelta(seconds=_int(token_data.get("expires_in")))).isoformat()
        admin.table("google_ads_connections").update(
            {
                "access_token": row["access_token"],
                "expires_at": row["expires_at"],
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", row["id"]).execute()
    return row


async def _google_get(settings: Settings, path: str, access_token: str, login_customer_id: str | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{_google_ads_base_url(settings)}/{path.lstrip('/')}",
            headers=_google_headers(settings, access_token, login_customer_id),
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=_error_message(response.json()))
    return response.json()


async def _google_search_stream(settings: Settings, customer_id: str, access_token: str, query: str, login_customer_id: str | None = None) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{_google_ads_base_url(settings)}/customers/{customer_id}/googleAds:searchStream",
            headers=_google_headers(settings, access_token, login_customer_id),
            json={"query": query},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=_error_message(response.json()))
    batches = response.json()
    rows: list[dict[str, Any]] = []
    if isinstance(batches, list):
        for batch in batches:
            rows.extend(batch.get("results", []))
    return rows


def _update_or_insert(client, table: str, match: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    existing = client.table(table).select("id").match(match).limit(1).execute()
    if existing.data:
        result = client.table(table).update(row).eq("id", existing.data[0]["id"]).execute()
    else:
        result = client.table(table).insert({**match, **row}).execute()
    return (result.data or [{}])[0]


@router.get("/status")
def google_ads_status(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, object]:
    settings = get_settings()
    missing = _missing_google_settings(settings)
    admin = get_supabase_admin()
    try:
        connection = (
            admin.table("google_ads_connections")
            .select("id,google_user_email,scopes,created_at,updated_at")
            .eq("owner_id", user.id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        accounts = (
            admin.table("google_ads_customer_accounts")
            .select("customer_id,descriptive_name,currency_code,time_zone,manager,created_at")
            .eq("owner_id", user.id)
            .order("descriptive_name")
            .execute()
        )
        schema_ready = True
    except APIError:
        connection = None
        accounts = None
        schema_ready = False
    return {
        "ok": True,
        "schemaReady": schema_ready,
        "configured": not missing,
        "missing": [*missing, *([] if schema_ready else ["SUPABASE_SCHEMA_GOOGLE_ADS"])],
        "connected": bool(connection and connection.data),
        "connection": ((connection.data or [None])[0] if connection else None),
        "accounts": accounts.data if accounts else [],
    }


@router.get("/oauth/start")
def start_google_ads_oauth(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, str]:
    settings = get_settings()
    _require_google_settings(settings)
    state = _sign_state(
        {
            "user_id": user.id,
            "nonce": secrets.token_urlsafe(16),
            "exp": int(time.time()) + 600,
        },
        settings.google_ads_client_secret,
    )
    params = {
        "client_id": settings.google_ads_client_id,
        "redirect_uri": _redirect_uri(settings),
        "response_type": "code",
        "scope": " ".join(settings.google_ads_scope_list),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"}


@router.get("/oauth/callback")
async def google_ads_oauth_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    error_description: str = Query(default=""),
) -> RedirectResponse:
    settings = get_settings()
    _require_google_settings(settings)
    frontend_url = settings.app_url.rstrip("/")

    if error:
        return RedirectResponse(f"{frontend_url}/?google_ads=error&message={urlencode({'m': error_description or error})}")

    payload = _read_state(state, settings.google_ads_client_secret)
    user_id = payload["user_id"]

    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "redirect_uri": _redirect_uri(settings),
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        if token_response.status_code >= 400:
            return RedirectResponse(f"{frontend_url}/?google_ads=error")

        token_data = token_response.json()
        profile_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

    profile = profile_response.json() if profile_response.status_code == 200 else {}
    admin = get_supabase_admin()
    google_user_id = profile.get("id") or profile.get("email") or user_id
    existing = (
        admin.table("google_ads_connections")
        .select("*")
        .eq("owner_id", user_id)
        .eq("google_user_id", google_user_id)
        .limit(1)
        .execute()
    )
    refresh_token = token_data.get("refresh_token") or ((existing.data or [{}])[0].get("refresh_token") or "")
    expires_at = (datetime.now(UTC) + timedelta(seconds=_int(token_data.get("expires_in")))).isoformat()
    admin.table("google_ads_connections").upsert(
        {
            "owner_id": user_id,
            "google_user_id": google_user_id,
            "google_user_email": profile.get("email") or "",
            "access_token": token_data["access_token"],
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "scopes": settings.google_ads_scope_list,
            "updated_at": datetime.now(UTC).isoformat(),
        },
        on_conflict="owner_id,google_user_id",
    ).execute()

    return RedirectResponse(f"{frontend_url}/?google_ads=connected")


@router.post("/refresh-accounts")
async def refresh_google_ads_accounts(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, object]:
    settings = get_settings()
    _require_google_settings(settings)
    admin = get_supabase_admin()
    connection = await _latest_connection(admin, user.id, settings)
    data = await _google_get(settings, "customers:listAccessibleCustomers", connection["access_token"])
    resource_names = data.get("resourceNames", [])
    saved_accounts: list[dict[str, Any]] = []
    for resource_name in resource_names:
        customer_id = _clean_customer_id(str(resource_name).split("/")[-1])
        if not customer_id:
            continue
        details = {
            "customer": {
                "id": customer_id,
                "descriptiveName": f"Google Ads {customer_id}",
                "currencyCode": None,
                "timeZone": None,
                "manager": False,
            }
        }
        try:
            rows = await _google_search_stream(
                settings,
                customer_id,
                connection["access_token"],
                (
                    "SELECT customer.id, customer.descriptive_name, customer.currency_code, "
                    "customer.time_zone, customer.manager FROM customer LIMIT 1"
                ),
                settings.google_ads_login_customer_id or customer_id,
            )
            if rows:
                details = rows[0]
        except HTTPException:
            pass
        customer = details.get("customer") or {}
        saved = _update_or_insert(
            admin,
            "google_ads_customer_accounts",
            {"owner_id": user.id, "customer_id": customer_id},
            {
                "descriptive_name": customer.get("descriptiveName") or customer.get("descriptive_name") or f"Google Ads {customer_id}",
                "currency_code": customer.get("currencyCode") or customer.get("currency_code"),
                "time_zone": customer.get("timeZone") or customer.get("time_zone"),
                "manager": bool(customer.get("manager")),
                "raw": details,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
        saved_accounts.append(saved)
    return {"ok": True, "accountsSynced": len(saved_accounts), "accounts": saved_accounts}


@router.post("/sync/{client_id}")
async def sync_google_ads_client(
    client_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    date_preset: str = Body(default="last_30d", embed=True),
    since: str | None = Body(default=None, embed=True),
    until: str | None = Body(default=None, embed=True),
) -> dict[str, object]:
    settings = get_settings()
    _require_google_settings(settings)
    admin = get_supabase_admin()
    client_result = (
        admin.table("clients")
        .select("*")
        .eq("id", client_id)
        .eq("owner_id", user.id)
        .limit(1)
        .execute()
    )
    if not client_result.data:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    client_row = client_result.data[0]
    customer_id = _clean_customer_id(client_row.get("google_ads_customer_id"))
    if not customer_id:
        raise HTTPException(status_code=400, detail="Cliente sem conta Google Ads vinculada.")

    connection = await _latest_connection(admin, user.id, settings)
    sync_run = admin.table("sync_runs").insert(
        {
            "owner_id": user.id,
            "client_id": client_id,
            "source": "google_ads",
            "status": "running",
        }
    ).execute()
    sync_run_id = sync_run.data[0]["id"] if sync_run.data else None

    try:
        period_since, period_until = _period_bounds(date_preset, since, until)
        campaigns_query = (
            "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, "
            "campaign_budget.amount_micros FROM campaign WHERE campaign.status != 'REMOVED'"
        )
        campaign_rows = await _google_search_stream(settings, customer_id, connection["access_token"], campaigns_query)
        campaign_id_by_external_id: dict[str, str] = {}
        for row in campaign_rows:
            campaign = row.get("campaign") or {}
            budget = row.get("campaignBudget") or row.get("campaign_budget") or {}
            external_id = str(campaign.get("id") or "")
            if not external_id:
                continue
            saved = _update_or_insert(
                admin,
                "campaigns",
                {"client_id": client_id, "platform": "google_ads", "external_id": external_id},
                {
                    "owner_id": user.id,
                    "organization_id": client_row.get("organization_id"),
                    "meta_campaign_id": None,
                    "ad_account_id": customer_id,
                    "name": campaign.get("name") or f"Campanha {external_id}",
                    "status": campaign.get("status"),
                    "effective_status": campaign.get("status"),
                    "objective": campaign.get("advertisingChannelType") or campaign.get("advertising_channel_type"),
                    "daily_budget": _num(budget.get("amountMicros") or budget.get("amount_micros")) / 1_000_000,
                    "metadata": row,
                    "raw": row,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            if saved.get("id"):
                campaign_id_by_external_id[external_id] = saved["id"]

        metrics_query = (
            "SELECT segments.date, campaign.id, campaign.name, metrics.cost_micros, metrics.impressions, "
            "metrics.clicks, metrics.conversions, metrics.ctr, metrics.average_cpc, metrics.average_cpm "
            "FROM campaign "
            f"WHERE segments.date BETWEEN '{period_since}' AND '{period_until}' "
            "AND campaign.status != 'REMOVED'"
        )
        metric_rows = await _google_search_stream(settings, customer_id, connection["access_token"], metrics_query)
        metrics_synced = 0
        for row in metric_rows:
            campaign = row.get("campaign") or {}
            metrics = row.get("metrics") or {}
            segments = row.get("segments") or {}
            external_id = str(campaign.get("id") or "")
            metric_date = segments.get("date")
            if not external_id or not metric_date:
                continue
            spend = _num(metrics.get("costMicros") or metrics.get("cost_micros")) / 1_000_000
            conversions = _int(metrics.get("conversions"))
            _update_or_insert(
                admin,
                "campaign_daily_metrics",
                {
                    "client_id": client_id,
                    "platform": "google_ads",
                    "metric_date": metric_date,
                    "campaign_external_id": external_id,
                },
                {
                    "owner_id": user.id,
                    "campaign_id": campaign_id_by_external_id.get(external_id),
                    "meta_campaign_id": None,
                    "source_file": f"google_ads_api_{date_preset}",
                    "date": metric_date,
                    "campaign": campaign.get("name") or f"Campanha {external_id}",
                    "campaign_name": campaign.get("name") or f"Campanha {external_id}",
                    "ad_group": "",
                    "ad_name": "",
                    "spend": spend,
                    "impressions": _int(metrics.get("impressions")),
                    "reach": 0,
                    "clicks": _int(metrics.get("clicks")),
                    "inline_link_clicks": _int(metrics.get("clicks")),
                    "leads": conversions,
                    "ctr": _num(metrics.get("ctr")) * 100 if _num(metrics.get("ctr")) <= 1 else _num(metrics.get("ctr")),
                    "cpc": _num(metrics.get("averageCpc") or metrics.get("average_cpc")) / 1_000_000,
                    "cpm": _num(metrics.get("averageCpm") or metrics.get("average_cpm")) / 1_000_000,
                    "frequency": 0,
                    "cpl": spend / conversions if conversions else 0,
                    "raw_json": {"source": "google_ads", **row},
                    "raw": row,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            metrics_synced += 1

        if sync_run_id:
            admin.table("sync_runs").update(
                {
                    "status": "success",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "campaigns_synced": len(campaign_rows),
                    "metrics_synced": metrics_synced,
                }
            ).eq("id", sync_run_id).execute()
        return {"ok": True, "campaignsSynced": len(campaign_rows), "metricsSynced": metrics_synced, "datePreset": date_preset}
    except (HTTPException, APIError) as exc:
        if sync_run_id:
            admin.table("sync_runs").update(
                {
                    "status": "error",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "error": _error_message(getattr(exc, "message", None) or getattr(exc, "detail", None) or exc),
                }
            ).eq("id", sync_run_id).execute()
        if isinstance(exc, HTTPException):
            raise HTTPException(status_code=exc.status_code, detail=_error_message(exc.detail)) from exc
        raise HTTPException(status_code=500, detail=exc.message) from exc
