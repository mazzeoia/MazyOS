from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.llm import MODEL_HAIKU, MODEL_SONNET, classify_intent, dispatch_tool, run_agent_turn


def test_classify_intent_simple():
    assert classify_intent("qual o CTR hoje?") == "simples"
    assert classify_intent("pode ativar") == "simples"


def test_classify_intent_strategy():
    assert classify_intent("quero criar uma campanha nova pro meu produto") == "estrategia"
    assert classify_intent("ajusta a verba da campanha") == "estrategia"


async def test_dispatch_tool_listar_contas(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    from app.agent.tools import ToolContext

    ctx = ToolContext(supabase=fake_supabase, settings=None, user_id="u1", conversation_id="c1", ad_account_id=None)
    result = await dispatch_tool("listar_contas", {}, ctx, meta_client=None)
    assert result == {"contas": []}


async def test_run_agent_turn_no_tool_call(monkeypatch, fake_supabase):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(type="text", text="Oi! Como posso ajudar?")]
    fake_message.stop_reason = "end_turn"
    fake_message.usage = MagicMock(input_tokens=120, output_tokens=15)

    fake_client = MagicMock()
    fake_client.messages.create = AsyncMock(return_value=fake_message)
    monkeypatch.setattr("app.agent.llm.anthropic.AsyncAnthropic", lambda **kw: fake_client)

    from app.agent.tools import ToolContext

    ctx = ToolContext(supabase=fake_supabase, settings=None, user_id="u1", conversation_id="c1", ad_account_id=None)
    result = await run_agent_turn(
        ctx=ctx, meta_client=None, resumo_memoria="", memoria_negocio={}, historico=[],
        mensagem_atual="oi", nivel_tecnico="leigo", anthropic_api_key="sk-ant-test", anthropic_workspace_id="",
    )
    assert result["resposta"] == "Oi! Como posso ajudar?"
    assert result["tokens_input"] == 120
    assert result["tokens_output"] == 15
    assert result["modelo_usado"] == MODEL_HAIKU
