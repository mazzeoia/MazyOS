"""Unit tests for app.agent.router.process_incoming_message — the background
task that does all the real work after a webhook has already ack'd."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent import router as agent_router
from app.agent.channels.base import IncomingMessage
from app.config import Settings


class FakeAdapter:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []
        self.downloaded: list[str] = []
        self.media = b"fake-audio"

    async def send_text(self, chat_id: str, text: str) -> None:
        self.sent.append((chat_id, text))

    async def receive_webhook(self, payload: dict) -> IncomingMessage:  # pragma: no cover
        raise NotImplementedError

    async def download_media(self, file_ref: str) -> bytes:
        self.downloaded.append(file_ref)
        return self.media


@pytest.fixture
def settings():
    return Settings(frontend_url="https://painel.exemplo.com", openai_api_key="sk-test")


@pytest.fixture
def adapter(monkeypatch):
    fake = FakeAdapter()
    monkeypatch.setattr(agent_router, "_adapter_for", lambda channel, settings: fake)
    return fake


def _wire(monkeypatch, *, conv, history=None, turn=None, duplicate=False):
    monkeypatch.setattr(agent_router, "get_or_create_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr(
        agent_router, "message_already_processed", AsyncMock(return_value=duplicate)
    )
    monkeypatch.setattr(
        agent_router, "get_recent_messages", AsyncMock(return_value=history or [])
    )
    recorded = AsyncMock()
    monkeypatch.setattr(agent_router, "record_message", recorded)
    run_turn = AsyncMock(
        return_value=turn
        or {
            "resposta": "beleza, já olhei",
            "modelo_usado": "claude-haiku-4-5",
            "tokens_input": 10,
            "tokens_output": 5,
        }
    )
    monkeypatch.setattr(agent_router, "run_agent_turn", run_turn)
    return recorded, run_turn


def _msg(**kwargs):
    base = dict(channel="telegram", channel_user_id="555", raw={"message": {"message_id": 1}}, text="oi")
    base.update(kwargs)
    return IncomingMessage(**base)


def _linked_supabase():
    supabase = MagicMock()
    supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"nivel_tecnico": "leigo"}
    ]
    return supabase


async def test_unlinked_conversation_sends_dashboard_login_message(monkeypatch, settings, adapter):
    _wire(monkeypatch, conv={"id": "conv-1", "owner_id": None})

    called = False

    def _boom(*a, **kw):  # pragma: no cover - must never run
        nonlocal called
        called = True
        return ""

    monkeypatch.setattr("app.auth.meta_oauth.generate_oauth_url", _boom)

    await process_or_fail(_msg(), settings, MagicMock())

    assert called is False
    assert len(adapter.sent) == 1
    text = adapter.sent[0][1]
    assert "painel.exemplo.com" in text
    assert "http" in text


async def test_unlinked_evolution_conversation_flags_experimental(monkeypatch, settings, adapter):
    _wire(monkeypatch, conv={"id": "conv-1", "owner_id": None})
    msg = _msg(channel="evolution", raw={"data": {"key": {"id": "EVT1"}}})

    await process_or_fail(msg, settings, MagicMock())

    assert "experimental" in adapter.sent[0][1].lower()


async def test_linked_conversation_normal_text_turn(monkeypatch, settings, adapter):
    history = [{"role": "user", "content": "antes"}, {"role": "assistant", "content": "resposta antiga"}]
    recorded, run_turn = _wire(
        monkeypatch, conv={"id": "conv-1", "owner_id": "user-1"}, history=history
    )

    await process_or_fail(_msg(), settings, _linked_supabase())

    _, kwargs = run_turn.call_args
    assert kwargs["historico"] == history
    assert kwargs["mensagem_atual"] == "oi"
    assert kwargs["nivel_tecnico"] == "leigo"

    papeis = [call.args[2] for call in recorded.call_args_list]
    assert papeis == ["user", "assistant"]
    assert adapter.sent == [("555", "beleza, já olhei")]


async def test_duplicate_webhook_is_skipped(monkeypatch, settings, adapter):
    recorded, run_turn = _wire(
        monkeypatch, conv={"id": "conv-1", "owner_id": "user-1"}, duplicate=True
    )

    await process_or_fail(_msg(), settings, _linked_supabase())

    run_turn.assert_not_called()
    recorded.assert_not_called()
    assert adapter.sent == []


async def test_audio_message_downloads_then_transcribes(monkeypatch, settings, adapter):
    recorded, run_turn = _wire(monkeypatch, conv={"id": "conv-1", "owner_id": "user-1"})
    transcribe = AsyncMock(return_value="quero ver minhas métricas")
    monkeypatch.setattr(agent_router, "transcribe_audio", transcribe)

    await process_or_fail(_msg(text=None, audio_ref="file-abc"), settings, _linked_supabase())

    assert adapter.downloaded == ["file-abc"]
    transcribe.assert_awaited_once_with(b"fake-audio", "sk-test")
    _, kwargs = run_turn.call_args
    assert kwargs["mensagem_atual"] == "quero ver minhas métricas"


async def test_transcription_failure_sends_fallback(monkeypatch, settings, adapter):
    recorded, run_turn = _wire(monkeypatch, conv={"id": "conv-1", "owner_id": "user-1"})
    monkeypatch.setattr(agent_router, "transcribe_audio", AsyncMock(side_effect=RuntimeError("boom")))

    await process_or_fail(_msg(text=None, audio_ref="file-abc"), settings, _linked_supabase())

    run_turn.assert_not_called()
    assert "áudio" in adapter.sent[0][1]


async def process_or_fail(msg, settings, supabase):
    await agent_router.process_incoming_message(msg, settings, supabase)
