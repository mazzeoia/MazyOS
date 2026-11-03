# app/agent/conversation.py
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone


async def get_or_create_conversation(supabase, channel: str, channel_user_id: str) -> dict:
    """Find the conversation for this channel+user, or create a fresh one.

    Uses upsert on the (channel, channel_user_id) unique constraint so two
    webhooks arriving at once can't race into a duplicate insert. Only the
    conflict keys are written, so an existing owner_id/ad_account_id is kept
    (owner_id stays NULL until the Meta OAuth callback links a real account).
    """
    rows = (
        supabase.table("conversations")
        .upsert(
            {"channel": channel, "channel_user_id": channel_user_id},
            on_conflict="channel,channel_user_id",
        )
        .execute()
        .data
    )
    if rows:
        return rows[0]

    return (
        supabase.table("conversations")
        .select("*")
        .eq("channel", channel)
        .eq("channel_user_id", channel_user_id)
        .execute()
        .data[0]
    )


async def record_message(
    supabase,
    conversation_id: str,
    papel: str,
    conteudo: str,
    *,
    media_url: str | None = None,
    external_message_id: str | None = None,
    transcricao: str | None = None,
    modelo_usado: str | None = None,
    tokens_input: int = 0,
    tokens_output: int = 0,
) -> None:
    supabase.table("messages").insert(
        {
            "conversation_id": conversation_id,
            "papel": papel,
            "conteudo": conteudo,
            "media_url": media_url,
            "external_message_id": external_message_id,
            "transcricao": transcricao,
            "modelo_usado": modelo_usado,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
        }
    ).execute()


async def get_recent_messages(supabase, conversation_id: str, limit: int = 10) -> list[dict]:
    """Last `limit` messages of this conversation, oldest first, shaped for the
    Anthropic messages array. Stored 'tool' rows are skipped: tool_use/tool_result
    blocks are rebuilt inside a single run_agent_turn and don't persist across turns."""
    rows = (
        supabase.table("messages")
        .select("papel,conteudo,criado_em")
        .eq("conversation_id", conversation_id)
        .order("criado_em", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    history = [
        {"role": row["papel"], "content": row["conteudo"]}
        for row in reversed(rows)
        if row.get("papel") in ("user", "assistant") and row.get("conteudo")
    ]
    return history


async def message_already_processed(supabase, conversation_id: str, external_message_id: str) -> bool:
    """Webhook idempotency — channels redeliver on timeout/retry."""
    rows = (
        supabase.table("messages")
        .select("id")
        .eq("conversation_id", conversation_id)
        .eq("external_message_id", external_message_id)
        .execute()
        .data
        or []
    )
    return bool(rows)


async def update_memory(
    supabase,
    conversation_id: str,
    *,
    resumo_memoria: str | None = None,
    memoria_negocio: dict | None = None,
) -> None:
    payload: dict = {"atualizado_em": datetime.now(timezone.utc).isoformat()}
    if resumo_memoria is not None:
        payload["resumo_memoria"] = resumo_memoria
    if memoria_negocio is not None:
        payload["memoria_negocio"] = memoria_negocio
    supabase.table("conversations").update(payload).eq("id", conversation_id).execute()


async def link_ad_account(supabase, conversation_id: str, ad_account_id: str) -> None:
    supabase.table("conversations").update({"ad_account_id": ad_account_id}).eq("id", conversation_id).execute()


async def generate_link_code(supabase, conversation_id: str, *, ttl_minutes: int = 15) -> str:
    """Create a short one-time numeric code for linking a chat conversation to a
    dashboard account. Stored directly on the conversation row — a conversation
    has at most one pending code at a time, so a separate table is unnecessary.
    """
    code = str(secrets.randbelow(900000) + 100000)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
    supabase.table("conversations").update(
        {"link_code": code, "link_code_expires_at": expires_at}
    ).eq("id", conversation_id).execute()
    return code


async def link_conversation_by_code(supabase, code: str, owner_id: str) -> dict | None:
    """Look up the conversation with this pending, unexpired link code and bind
    it to `owner_id`, clearing the code so it can't be reused. Returns the
    linked conversation row, or None if the code is unknown/expired.
    """
    now = datetime.now(timezone.utc).isoformat()
    rows = (
        supabase.table("conversations")
        .select("*")
        .eq("link_code", code)
        .gt("link_code_expires_at", now)
        .execute()
        .data
        or []
    )
    if not rows:
        return None

    conv = rows[0]
    supabase.table("conversations").update(
        {"owner_id": owner_id, "link_code": None, "link_code_expires_at": None}
    ).eq("id", conv["id"]).execute()
    conv["owner_id"] = owner_id
    return conv
