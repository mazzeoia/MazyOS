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
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi.responses import RedirectResponse
from postgrest.exceptions import APIError

from ..auth import CurrentUser, get_current_user
from ..config import Settings, get_settings
from ..supabase_client import get_supabase_admin


router = APIRouter(prefix="/meta", tags=["meta"])


def _period_query(period: str, since: str | None = None, until: str | None = None) -> dict[str, str]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    if period == "today":
        return {"time_range": json.dumps({"since": today.isoformat(), "until": today.isoformat()})}
    if period == "yesterday":
        return {"time_range": json.dumps({"since": yesterday.isoformat(), "until": yesterday.isoformat()})}
    if period == "last_7d":
        return {"time_range": json.dumps({"since": (yesterday - timedelta(days=6)).isoformat(), "until": yesterday.isoformat()})}
    if period == "maximum":
        return {"date_preset": "maximum"}
    if period == "custom":
        if not since or not until:
            raise HTTPException(status_code=400, detail="Informe data inicial e final.")
        return {"time_range": json.dumps({"since": since, "until": until})}
    return {"time_range": json.dumps({"since": (yesterday - timedelta(days=29)).isoformat(), "until": yesterday.isoformat()})}


def _period_bounds(period: str, since: str | None = None, until: str | None = None) -> tuple[str | None, str | None]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    if period == "today":
        return today.isoformat(), today.isoformat()
    if period == "yesterday":
        return yesterday.isoformat(), yesterday.isoformat()
    if period == "last_7d":
        return (yesterday - timedelta(days=6)).isoformat(), yesterday.isoformat()
    if period == "custom":
        return since, until
    if period == "maximum":
        return None, None
    return (yesterday - timedelta(days=29)).isoformat(), yesterday.isoformat()


def _previous_period_bounds(period: str, since: str | None = None, until: str | None = None) -> tuple[str | None, str | None]:
    current_since, current_until = _period_bounds(period, since, until)
    if not current_since or not current_until:
        return None, None
    start = date.fromisoformat(current_since)
    end = date.fromisoformat(current_until)
    days = (end - start).days + 1
    previous_until = start - timedelta(days=1)
    previous_since = previous_until - timedelta(days=days - 1)
    return previous_since.isoformat(), previous_until.isoformat()


def _graph_url(settings: Settings, path: str) -> str:
    return f"https://graph.facebook.com/{settings.meta_api_version}/{path.lstrip('/')}"


def _redirect_uri(settings: Settings) -> str:
    return f"{settings.app_url.rstrip('/')}/api/meta/oauth/callback"


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


async def _graph_get(path: str, access_token: str, fields: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    params: dict[str, str] = {"access_token": access_token}
    if fields:
        params["fields"] = fields

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(_graph_url(settings, path), params=params)

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=_error_message(response.json()))
    return response.json()


async def _graph_get_all(path: str, access_token: str, fields: str | None = None, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    query: dict[str, str] = {"access_token": access_token, "limit": "100"}
    if fields:
        query["fields"] = fields
    if params:
        query.update(params)

    rows: list[dict[str, Any]] = []
    url = _graph_url(settings, path)
    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            response = await client.get(url, params=query)
            query = {}
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=_error_message(response.json()))
            data = response.json()
            rows.extend(data.get("data", []))
            url = data.get("paging", {}).get("next", "")
    return rows


def _extract_leads(actions: list[dict[str, Any]] | None) -> int:
    if not actions:
        return 0
    lead_action_types = {
        "lead",
        "onsite_conversion.lead",
        "onsite_conversion.lead_grouped",
        "offsite_conversion.fb_pixel_lead",
    }
    return sum(int(float(action.get("value", 0) or 0)) for action in actions if action.get("action_type") in lead_action_types)


def _extract_conversations(actions: list[dict[str, Any]] | None) -> int:
    if not actions:
        return 0
    conversation_action_types = {"onsite_conversion.messaging_conversation_started_7d"}
    return sum(int(float(action.get("value", 0) or 0)) for action in actions if action.get("action_type") in conversation_action_types)


def _extract_meta_results(actions: list[dict[str, Any]] | None) -> tuple[str, int]:
    result_action_priority = [
        ("Conversas", {"onsite_conversion.messaging_conversation_started_7d"}),
        ("Leads", {"lead", "onsite_conversion.lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead"}),
        ("Cliques no link", {"link_click"}),
    ]
    for label, action_types in result_action_priority:
        value = sum(int(float(action.get("value", 0) or 0)) for action in actions if action.get("action_type") in action_types)
        if value:
            return label, value
    return "Resultados", 0


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


def _error_message(detail: Any) -> str:
    if isinstance(detail, dict):
        error = detail.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(detail.get("message") or detail)
    return str(detail)


def _creative_preview_from_ad(ad: dict[str, Any]) -> dict[str, Any]:
    creative = ad.get("creative") if isinstance(ad.get("creative"), dict) else {}
    adset = ad.get("adset") if isinstance(ad.get("adset"), dict) else {}
    image_url = creative.get("image_url") or creative.get("thumbnail_url")
    return {
        "ad_id": ad.get("id"),
        "ad_name": ad.get("name") or creative.get("name") or "Criativo sem nome",
        "adset_id": ad.get("adset_id"),
        "adset_name": adset.get("name") or "",
        "creative_id": creative.get("id"),
        "creative_name": creative.get("name") or "",
        "image_url": image_url,
        "thumbnail_url": creative.get("thumbnail_url") or image_url,
        "status": ad.get("effective_status") or ad.get("status"),
    }


def _canonical_ad_account_id(value: str | None) -> str | None:
    clean = (value or "").strip()
    if not clean:
        return None
    normalized = clean.removeprefix("act_")
    return f"act_{normalized}" if normalized.isdigit() else clean


def _account_merge_key(account: dict[str, Any]) -> str:
    account_id = str(account.get("account_id") or account.get("id") or "")
    return account_id.removeprefix("act_")


def _merge_ad_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for account in accounts:
        key = _account_merge_key(account)
        if not key:
            continue
        current = merged.get(key, {})
        merged[key] = {**current, **account}
    return sorted(merged.values(), key=lambda item: str(item.get("name") or "").lower())


METRICS_SELECT = (
    "campaign_external_id,campaign_name,campaign,platform,ad_group,ad_name,spend,impressions,reach,"
    "clicks,inline_link_clicks,leads,metric_date,raw_json"
)


def _update_or_insert(client, table: str, match: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    existing = client.table(table).select("id").match(match).limit(1).execute()
    if existing.data:
        result = client.table(table).update(row).eq("id", existing.data[0]["id"]).execute()
    else:
        result = client.table(table).insert({**match, **row}).execute()
    return (result.data or [{}])[0]


def _require_meta_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "META_APP_ID": settings.meta_app_id,
            "META_APP_SECRET": settings.meta_app_secret,
            "SUPABASE_SECRET_KEY": settings.supabase_secret_key,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f"Configure: {', '.join(missing)}.")


@router.get("/webhook", response_class=PlainTextResponse)
def verify_meta_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> str:
    settings = get_settings()
    if not settings.meta_webhook_verify_token:
        raise HTTPException(status_code=500, detail="Configure META_WEBHOOK_VERIFY_TOKEN.")

    if hub_mode == "subscribe" and hmac.compare_digest(hub_verify_token, settings.meta_webhook_verify_token):
        return hub_challenge

    raise HTTPException(status_code=403, detail="Webhook verify token invalido.")


@router.post("/webhook")
async def receive_meta_webhook(request: Request) -> dict[str, object]:
    payload = await request.json()
    # A V1 apenas recebe os eventos; a persistencia por tipo de evento entra na sincronizacao.
    return {"ok": True, "received": bool(payload)}


@router.get("/oauth/start")
def start_meta_oauth(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict[str, str]:
    settings = get_settings()
    _require_meta_settings(settings)

    state = _sign_state(
        {
            "user_id": user.id,
            "nonce": secrets.token_urlsafe(16),
            "exp": int(time.time()) + 600,
        },
        settings.meta_app_secret,
    )
    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": _redirect_uri(settings),
        "state": state,
        "scope": ",".join(settings.meta_scope_list),
        "response_type": "code",
    }
    return {"url": f"https://www.facebook.com/{settings.meta_api_version}/dialog/oauth?{urlencode(params)}"}


@router.get("/oauth/callback")
async def meta_oauth_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    error_description: str = Query(default=""),
) -> RedirectResponse:
    settings = get_settings()
    _require_meta_settings(settings)
    frontend_url = settings.app_url.rstrip("/")

    if error:
        return RedirectResponse(f"{frontend_url}/?meta=error&message={urlencode({'m': error_description or error})}")

    payload = _read_state(state, settings.meta_app_secret)
    user_id = payload["user_id"]

    async with httpx.AsyncClient(timeout=20) as client:
        short_response = await client.get(
            _graph_url(settings, "oauth/access_token"),
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": _redirect_uri(settings),
                "code": code,
            },
        )
        if short_response.status_code >= 400:
            return RedirectResponse(f"{frontend_url}/?meta=error")

        short_token = short_response.json()["access_token"]
        long_response = await client.get(
            _graph_url(settings, "oauth/access_token"),
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        if long_response.status_code >= 400:
            return RedirectResponse(f"{frontend_url}/?meta=error")

    token_data = long_response.json()
    access_token = token_data["access_token"]
    profile = await _graph_get("me", access_token, fields="id,name,email")

    admin = get_supabase_admin()
    admin.table("meta_connections").upsert(
        {
            "owner_id": user_id,
            "meta_user_id": profile.get("id"),
            "meta_user_name": profile.get("name"),
            "access_token": access_token,
            "expires_at": None,
            "scopes": settings.meta_scope_list,
        },
        on_conflict="owner_id,meta_user_id",
    ).execute()

    return RedirectResponse(f"{frontend_url}/?meta=connected")


def _cached_meta_assets(admin, owner_id: str) -> dict[str, Any]:
    businesses_result = (
        admin.table("meta_businesses")
        .select("meta_business_id,name,verification_status")
        .eq("owner_id", owner_id)
        .order("name")
        .execute()
    )
    business_by_id = {
        row.get("meta_business_id"): {
            "id": row.get("meta_business_id"),
            "name": row.get("name"),
            "verification_status": row.get("verification_status"),
        }
        for row in businesses_result.data or []
    }
    accounts_result = (
        admin.table("meta_ad_accounts")
        .select("meta_ad_account_id,account_id,name,account_status,currency,timezone_name,business_id,raw")
        .eq("owner_id", owner_id)
        .order("name")
        .execute()
    )
    pages_result = (
        admin.table("meta_pages")
        .select("meta_page_id,name,category,meta_instagram_account_id,instagram_username")
        .eq("owner_id", owner_id)
        .order("name")
        .execute()
    )
    ad_accounts = []
    for row in accounts_result.data or []:
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        business = business_by_id.get(row.get("business_id")) or raw.get("business")
        ad_accounts.append(
            {
                "id": row.get("meta_ad_account_id"),
                "account_id": row.get("account_id"),
                "name": row.get("name"),
                "account_status": row.get("account_status"),
                "currency": row.get("currency"),
                "timezone_name": row.get("timezone_name"),
                "business": business,
            }
        )
    pages = [
        {
            "id": row.get("meta_page_id"),
            "name": row.get("name"),
            "category": row.get("category"),
            "instagram_business_account": (
                {
                    "id": row.get("meta_instagram_account_id"),
                    "username": row.get("instagram_username"),
                    "name": row.get("instagram_username"),
                }
                if row.get("meta_instagram_account_id")
                else None
            ),
        }
        for row in pages_result.data or []
    ]
    return {
        "businesses": list(business_by_id.values()),
        "adAccounts": ad_accounts,
        "pages": pages,
    }


@router.get("/assets")
async def list_meta_assets(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    refresh: bool = Query(default=False),
) -> dict[str, object]:
    admin = get_supabase_admin()
    connection = (
        admin.table("meta_connections")
        .select("*")
        .eq("owner_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not connection.data:
        return {"ok": True, "connected": False, "businesses": [], "adAccounts": [], "pages": []}

    cached = _cached_meta_assets(admin, user.id)
    if not refresh and (cached["adAccounts"] or cached["pages"] or cached["businesses"]):
        return {
            "ok": True,
            "connected": True,
            "cached": True,
            **cached,
        }

    token = connection.data[0]["access_token"]
    businesses = await _graph_get_all("me/businesses", token, fields="id,name,verification_status")
    direct_ad_accounts = await _graph_get_all(
        "me/adaccounts",
        token,
        fields="id,account_id,name,account_status,currency,timezone_name,business{id,name}",
    )
    business_ad_accounts: list[dict[str, Any]] = []
    for business in businesses:
        business_id = business.get("id")
        if not business_id:
            continue
        for edge in ("owned_ad_accounts", "client_ad_accounts"):
            try:
                rows = await _graph_get_all(
                    f"{business_id}/{edge}",
                    token,
                    fields="id,account_id,name,account_status,currency,timezone_name,business{id,name}",
                )
            except HTTPException:
                continue
            for row in rows:
                row.setdefault("business", {"id": business_id, "name": business.get("name")})
                row["business_source"] = edge
                business_ad_accounts.append(row)
    pages = await _graph_get(
        "me/accounts",
        token,
        fields="id,name,category,access_token,instagram_business_account{id,username,name}",
    )
    ad_accounts = _merge_ad_accounts([*direct_ad_accounts, *business_ad_accounts])
    for business in businesses:
        if business.get("id") and business.get("name"):
            admin.table("meta_businesses").upsert(
                {
                    "owner_id": connection.data[0]["owner_id"],
                    "meta_business_id": business.get("id"),
                    "name": business.get("name"),
                    "verification_status": business.get("verification_status"),
                    "raw": business,
                },
                on_conflict="owner_id,meta_business_id",
            ).execute()
    for account in ad_accounts:
        if account.get("id") and account.get("name"):
            business = account.get("business") if isinstance(account.get("business"), dict) else {}
            admin.table("meta_ad_accounts").upsert(
                {
                    "owner_id": connection.data[0]["owner_id"],
                    "meta_ad_account_id": account.get("id"),
                    "account_id": account.get("account_id"),
                    "name": account.get("name"),
                    "account_status": account.get("account_status"),
                    "currency": account.get("currency"),
                    "timezone_name": account.get("timezone_name"),
                    "business_id": business.get("id"),
                    "raw": account,
                },
                on_conflict="owner_id,meta_ad_account_id",
            ).execute()
    for page in pages.get("data", []):
        instagram = page.get("instagram_business_account") if isinstance(page.get("instagram_business_account"), dict) else {}
        if page.get("id") and page.get("name"):
            admin.table("meta_pages").upsert(
                {
                    "owner_id": connection.data[0]["owner_id"],
                    "meta_page_id": page.get("id"),
                    "name": page.get("name"),
                    "category": page.get("category"),
                    "meta_instagram_account_id": instagram.get("id"),
                    "instagram_username": instagram.get("username") or instagram.get("name"),
                    "raw": page,
                },
                on_conflict="owner_id,meta_page_id",
            ).execute()

    return {
        "ok": True,
        "connected": True,
        "businesses": businesses,
        "adAccounts": ad_accounts,
        "pages": pages.get("data", []),
    }


@router.post("/sync/{client_id}")
async def sync_meta_client(
    client_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    campaign_ids: list[str] = Body(default_factory=list, embed=True),
    date_preset: str = Body(default="last_30d", embed=True),
    since: str | None = Body(default=None, embed=True),
    until: str | None = Body(default=None, embed=True),
) -> dict[str, object]:
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
    ad_account_id = _canonical_ad_account_id(client_row.get("meta_ad_account_id"))
    if not ad_account_id:
        raise HTTPException(status_code=400, detail="Cliente sem conta Meta vinculada.")

    connection = (
        admin.table("meta_connections")
        .select("*")
        .eq("owner_id", user.id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not connection.data:
        raise HTTPException(status_code=400, detail="Conecte a Meta antes de sincronizar.")

    token = connection.data[0]["access_token"]
    sync_run = admin.table("sync_runs").insert(
        {
            "owner_id": user.id,
            "client_id": client_id,
            "source": "meta",
            "status": "running",
        }
    ).execute()
    sync_run_id = sync_run.data[0]["id"] if sync_run.data else None

    try:
        selected_campaign_ids = set(campaign_ids)
        campaigns = await _graph_get_all(
            f"{ad_account_id}/campaigns",
            token,
            fields="id,name,status,effective_status,objective,daily_budget,lifetime_budget,created_time,updated_time",
        )

        campaign_id_by_meta_id: dict[str, str] = {}
        for campaign in campaigns:
            saved = _update_or_insert(
                admin,
                "campaigns",
                {"client_id": client_id, "meta_campaign_id": campaign["id"]},
                {
                    "owner_id": user.id,
                    "organization_id": client_row.get("organization_id"),
                    "platform": "meta_ads",
                    "external_id": campaign["id"],
                    "name": campaign.get("name") or "Campanha sem nome",
                    "status": campaign.get("effective_status") or campaign.get("status"),
                    "effective_status": campaign.get("effective_status") or campaign.get("status"),
                    "objective": campaign.get("objective"),
                    "daily_budget": _num(campaign.get("daily_budget")) / 100 if campaign.get("daily_budget") else 0,
                    "lifetime_budget": _num(campaign.get("lifetime_budget")) / 100 if campaign.get("lifetime_budget") else 0,
                    "metadata": campaign,
                    "raw": campaign,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            if saved.get("id"):
                campaign_id_by_meta_id[campaign["id"]] = saved["id"]

        creative_previews_by_campaign: dict[str, list[dict[str, Any]]] = {}
        try:
            ads = await _graph_get_all(
                f"{ad_account_id}/ads",
                token,
                fields=(
                    "id,name,status,effective_status,campaign_id,adset_id,"
                    "adset{name},creative{id,name,thumbnail_url,image_url,effective_object_story_id}"
                ),
                params={"limit": "100"},
            )
            for ad in ads:
                meta_campaign_id = ad.get("campaign_id")
                if not meta_campaign_id:
                    continue
                if selected_campaign_ids and meta_campaign_id not in selected_campaign_ids:
                    continue
                preview = _creative_preview_from_ad(ad)
                if not preview.get("image_url"):
                    continue
                previews = creative_previews_by_campaign.setdefault(meta_campaign_id, [])
                if not any(item.get("ad_id") == preview.get("ad_id") for item in previews):
                    previews.append(preview)
            for campaign in campaigns:
                meta_campaign_id = campaign.get("id")
                previews = creative_previews_by_campaign.get(meta_campaign_id or "", [])[:6]
                if not meta_campaign_id or not previews:
                    continue
                metadata = {**campaign, "creative_previews": previews}
                admin.table("campaigns").update(
                    {"metadata": metadata, "updated_at": datetime.now(UTC).isoformat()}
                ).eq("client_id", client_id).eq("meta_campaign_id", meta_campaign_id).execute()
        except HTTPException:
            creative_previews_by_campaign = {}

        insights = await _graph_get_all(
            f"{ad_account_id}/insights",
            token,
            fields=(
                "campaign_id,campaign_name,date_start,date_stop,spend,impressions,reach,clicks,"
                "inline_link_clicks,ctr,cpc,cpm,frequency,actions,action_values,purchase_roas"
            ),
            params={"level": "campaign", "time_increment": "1", **_period_query(date_preset, since, until)},
        )

        metrics_synced = 0
        for insight in insights:
            meta_campaign_id = insight.get("campaign_id")
            metric_date = insight.get("date_start")
            if not meta_campaign_id or not metric_date:
                continue
            if selected_campaign_ids and meta_campaign_id not in selected_campaign_ids:
                continue
            campaign_label = insight.get("campaign_name") or meta_campaign_id
            _update_or_insert(
                admin,
                "campaign_daily_metrics",
                {
                    "client_id": client_id,
                    "platform": "meta_ads",
                    "metric_date": metric_date,
                    "campaign_external_id": meta_campaign_id,
                },
                {
                    "owner_id": user.id,
                    "campaign_id": campaign_id_by_meta_id.get(meta_campaign_id),
                    "meta_campaign_id": meta_campaign_id,
                    "source_file": f"meta_api_{date_preset}",
                    "date": metric_date,
                    "campaign": campaign_label,
                    "campaign_name": campaign_label,
                    "ad_group": "",
                    "ad_name": "",
                    "campaign_external_id": meta_campaign_id,
                    "spend": _num(insight.get("spend")),
                    "impressions": _int(insight.get("impressions")),
                    "reach": _int(insight.get("reach")),
                    "clicks": _int(insight.get("clicks")),
                    "inline_link_clicks": _int(insight.get("inline_link_clicks")),
                    "leads": _extract_leads(insight.get("actions")),
                    "ctr": _num(insight.get("ctr")),
                    "cpc": _num(insight.get("cpc")),
                    "cpm": _num(insight.get("cpm")),
                    "frequency": _num(insight.get("frequency")),
                    "cpl": (_num(insight.get("spend")) / _extract_leads(insight.get("actions"))) if _extract_leads(insight.get("actions")) else 0,
                    "raw_json": insight,
                    "raw": insight,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            metrics_synced += 1

        if sync_run_id:
            admin.table("sync_runs").update(
                {
                    "status": "success",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "campaigns_synced": len(campaigns),
                    "metrics_synced": metrics_synced,
                }
            ).eq("id", sync_run_id).execute()

        return {
            "ok": True,
            "campaignsSynced": len(campaigns),
            "metricsSynced": metrics_synced,
            "selectedCampaigns": len(selected_campaign_ids),
            "datePreset": date_preset,
        }
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


@router.get("/summary/{client_id}")
def meta_client_summary(
    client_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    date_preset: str = Query(default="last_30d"),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
) -> dict[str, object]:
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

    campaigns = (
        admin.table("campaigns")
        .select("id,name,status,effective_status,objective,meta_campaign_id,external_id,platform,metadata,updated_at")
        .eq("client_id", client_id)
        .order("updated_at", desc=True)
        .limit(100)
        .execute()
    )
    metrics_query = (
        admin.table("campaign_daily_metrics")
        .select(METRICS_SELECT)
        .eq("client_id", client_id)
    )
    period_since, period_until = _period_bounds(date_preset, since, until)
    if period_since:
        metrics_query = metrics_query.gte("metric_date", period_since)
    if period_until:
        metrics_query = metrics_query.lte("metric_date", period_until)
    metrics = metrics_query.execute()
    previous_metrics_query = (
        admin.table("campaign_daily_metrics")
        .select(METRICS_SELECT)
        .eq("client_id", client_id)
    )
    previous_since, previous_until = _previous_period_bounds(date_preset, since, until)
    if previous_since:
        previous_metrics_query = previous_metrics_query.gte("metric_date", previous_since)
    if previous_until:
        previous_metrics_query = previous_metrics_query.lte("metric_date", previous_until)
    previous_metrics = previous_metrics_query.execute() if previous_since and previous_until else None
    sync_runs = (
        admin.table("sync_runs")
        .select("*")
        .eq("client_id", client_id)
        .order("started_at", desc=True)
        .limit(5)
        .execute()
    )

    rows = metrics.data or []
    spend = sum(_num(row.get("spend")) for row in rows)
    leads = sum(_int(row.get("leads")) for row in rows)
    conversations = sum(_extract_conversations((row.get("raw_json") or {}).get("actions")) for row in rows)
    clicks = sum(_int(row.get("clicks")) for row in rows)
    impressions = sum(_int(row.get("impressions")) for row in rows)
    reach = sum(_int(row.get("reach")) for row in rows)
    if conversations:
        result_label = "Conversas"
        meta_results = conversations
    elif leads:
        result_label = "Leads"
        meta_results = leads
    else:
        result_labels = [_extract_meta_results((row.get("raw_json") or {}).get("actions")) for row in rows]
        result_label = next((label for label, value in result_labels if value), "Resultados")
        meta_results = sum(value for _label, value in result_labels)

    return {
        "ok": True,
        "client": client_result.data[0],
        "campaigns": campaigns.data or [],
        "metrics": rows,
        "previousMetrics": (previous_metrics.data if previous_metrics else []) or [],
        "syncRuns": sync_runs.data or [],
        "period": {"datePreset": date_preset, "since": period_since, "until": period_until},
        "previousPeriod": {"since": previous_since, "until": previous_until},
        "totals": {
            "spend": spend,
            "leads": leads,
            "conversations": conversations,
            "metaResults": meta_results,
            "resultLabel": result_label,
            "reach": reach,
            "clicks": clicks,
            "impressions": impressions,
            "cpl": spend / leads if leads else 0,
            "costPerResult": spend / meta_results if meta_results else 0,
            "cpm": (spend / impressions * 1000) if impressions else 0,
            "ctr": (clicks / impressions * 100) if impressions else 0,
        },
    }
