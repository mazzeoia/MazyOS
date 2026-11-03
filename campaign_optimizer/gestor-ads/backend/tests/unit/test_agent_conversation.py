from unittest.mock import MagicMock

import pytest

from app.agent.conversation import (
    generate_link_code,
    get_or_create_conversation,
    get_recent_messages,
    link_ad_account,
    link_conversation_by_code,
    message_already_processed,
    record_message,
    update_memory,
)


async def test_get_or_create_conversation_upserts(fake_supabase):
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.data = [
        {"id": "conv-1", "owner_id": "user-1", "ad_account_id": None, "resumo_memoria": "", "memoria_negocio": {}}
    ]
    row = await get_or_create_conversation(fake_supabase, "telegram", "555")
    assert row["id"] == "conv-1"
    args, kwargs = fake_supabase.table.return_value.upsert.call_args
    assert args[0] == {"channel": "telegram", "channel_user_id": "555"}
    assert kwargs["on_conflict"] == "channel,channel_user_id"


async def test_get_or_create_conversation_falls_back_to_select(fake_supabase):
    fake_supabase.table.return_value.upsert.return_value.execute.return_value.data = []
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "conv-new", "owner_id": None}
    ]
    row = await get_or_create_conversation(fake_supabase, "telegram", "555")
    assert row["id"] == "conv-new"


async def test_get_recent_messages_skips_tool_rows(fake_supabase):
    chain = fake_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value
    chain.execute.return_value.data = [
        {"papel": "assistant", "conteudo": "proposta pronta"},
        {"papel": "tool", "conteudo": "{}"},
        {"papel": "user", "conteudo": "quero uma campanha"},
    ]
    history = await get_recent_messages(fake_supabase, "conv-1")
    assert history == [
        {"role": "user", "content": "quero uma campanha"},
        {"role": "assistant", "content": "proposta pronta"},
    ]


async def test_message_already_processed(fake_supabase):
    chain = fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value
    chain.execute.return_value.data = [{"id": "m1"}]
    assert await message_already_processed(fake_supabase, "conv-1", "ext-1") is True
    chain.execute.return_value.data = []
    assert await message_already_processed(fake_supabase, "conv-1", "ext-1") is False


async def test_record_message(fake_supabase):
    await record_message(fake_supabase, "conv-1", "user", "oi", tokens_input=10)
    fake_supabase.table.assert_any_call("messages")


async def test_update_memory(fake_supabase):
    await update_memory(fake_supabase, "conv-1", resumo_memoria="resumo novo")
    fake_supabase.table.assert_any_call("conversations")


async def test_link_ad_account(fake_supabase):
    await link_ad_account(fake_supabase, "conv-1", "acc-1")
    fake_supabase.table.assert_any_call("conversations")


async def test_generate_link_code_is_six_digits(fake_supabase):
    code = await generate_link_code(fake_supabase, "conv-1")
    assert len(code) == 6
    assert code.isdigit()
    fake_supabase.table.assert_any_call("conversations")
    args, kwargs = fake_supabase.table.return_value.update.call_args
    assert args[0]["link_code"] == code
    assert "link_code_expires_at" in args[0]


async def test_generate_link_code_sets_expiry_in_future(fake_supabase):
    from datetime import datetime, timezone

    await generate_link_code(fake_supabase, "conv-1")
    args, kwargs = fake_supabase.table.return_value.update.call_args
    expires_at = datetime.fromisoformat(args[0]["link_code_expires_at"])
    assert expires_at > datetime.now(timezone.utc)


async def test_link_conversation_by_code_success(fake_supabase):
    chain = fake_supabase.table.return_value.select.return_value.eq.return_value.gt.return_value
    chain.execute.return_value.data = [
        {"id": "conv-1", "channel": "telegram", "channel_user_id": "555", "owner_id": None}
    ]
    conv = await link_conversation_by_code(fake_supabase, "482913", "user-1")
    assert conv["id"] == "conv-1"
    assert conv["owner_id"] == "user-1"
    args, kwargs = fake_supabase.table.return_value.update.call_args
    assert args[0]["owner_id"] == "user-1"
    assert args[0]["link_code"] is None
    assert args[0]["link_code_expires_at"] is None


async def test_link_conversation_by_code_not_found(fake_supabase):
    chain = fake_supabase.table.return_value.select.return_value.eq.return_value.gt.return_value
    chain.execute.return_value.data = []
    conv = await link_conversation_by_code(fake_supabase, "000000", "user-1")
    assert conv is None
