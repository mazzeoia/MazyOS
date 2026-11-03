from __future__ import annotations

import pytest

from app.agent.channels.base import ChannelAdapter, IncomingMessage


def test_incoming_message_defaults():
    msg = IncomingMessage(channel="telegram", channel_user_id="123", text="oi", raw={})
    assert msg.audio_ref is None
    assert msg.location is None


def test_channel_adapter_is_a_protocol():
    class FakeAdapter:
        async def send_text(self, chat_id: str, text: str) -> None: ...
        async def receive_webhook(self, payload: dict) -> IncomingMessage: ...
        async def download_media(self, file_ref: str) -> bytes: ...

    adapter: ChannelAdapter = FakeAdapter()
    assert isinstance(adapter, ChannelAdapter)


import respx
from httpx import Response

from app.agent.channels.telegram import TelegramAdapter


@respx.mock
async def test_telegram_send_text():
    respx.post("https://api.telegram.org/botTEST/sendMessage").mock(
        return_value=Response(200, json={"ok": True})
    )
    adapter = TelegramAdapter(bot_token="TEST")
    await adapter.send_text("chat123", "olá")
    assert respx.calls.last.request.headers["content-type"].startswith("application/json")


async def test_telegram_receive_webhook_text():
    adapter = TelegramAdapter(bot_token="TEST")
    payload = {
        "message": {
            "chat": {"id": 555},
            "text": "quero criar uma campanha",
        }
    }
    msg = await adapter.receive_webhook(payload)
    assert msg.channel == "telegram"
    assert msg.channel_user_id == "555"
    assert msg.text == "quero criar uma campanha"
    assert msg.audio_ref is None


async def test_telegram_receive_webhook_location():
    adapter = TelegramAdapter(bot_token="TEST")
    payload = {
        "message": {
            "chat": {"id": 555},
            "location": {"latitude": -3.7319, "longitude": -38.5267},
        }
    }
    msg = await adapter.receive_webhook(payload)
    assert msg.location == (-3.7319, -38.5267)


@respx.mock
async def test_telegram_download_media():
    respx.get("https://api.telegram.org/botTEST/getFile", params={"file_id": "abc"}).mock(
        return_value=Response(200, json={"ok": True, "result": {"file_path": "voice/file.oga"}})
    )
    respx.get("https://api.telegram.org/file/botTEST/voice/file.oga").mock(
        return_value=Response(200, content=b"fake-audio-bytes")
    )
    adapter = TelegramAdapter(bot_token="TEST")
    data = await adapter.download_media("abc")
    assert data == b"fake-audio-bytes"


from app.agent.channels.evolution import EvolutionAdapter


@respx.mock
async def test_evolution_send_text():
    respx.post("http://evolution:8080/message/sendText/creative-ads").mock(
        return_value=Response(200, json={"status": "success"})
    )
    adapter = EvolutionAdapter(base_url="http://evolution:8080", api_key="evo-key", instance="creative-ads")
    await adapter.send_text("558599999999", "olá")
    call = respx.calls.last
    assert call.request.headers["apikey"] == "evo-key"


async def test_evolution_receive_webhook_text():
    adapter = EvolutionAdapter(base_url="http://evolution:8080", api_key="evo-key", instance="creative-ads")
    payload = {
        "data": {
            "key": {"remoteJid": "558599999999@s.whatsapp.net"},
            "message": {"conversation": "quero ver minhas métricas"},
        }
    }
    msg = await adapter.receive_webhook(payload)
    assert msg.channel == "evolution"
    assert msg.channel_user_id == "558599999999"
    assert msg.text == "quero ver minhas métricas"


async def test_telegram_receive_webhook_audio_sets_ref_without_downloading():
    """The webhook handler must NOT download media — only carry the ref."""
    adapter = TelegramAdapter(bot_token="TEST")
    called = False

    async def _boom(file_ref):  # pragma: no cover - must never run
        nonlocal called
        called = True
        return b""

    adapter.download_media = _boom
    payload = {"message": {"chat": {"id": 555}, "voice": {"file_id": "abc"}}}
    msg = await adapter.receive_webhook(payload)
    assert msg.audio_ref == "abc"
    assert called is False


async def test_evolution_receive_webhook_extended_text():
    adapter = EvolutionAdapter(base_url="http://evolution:8080", api_key="evo-key", instance="creative-ads")
    payload = {
        "data": {
            "key": {"remoteJid": "558599999999@s.whatsapp.net"},
            "message": {"extendedTextMessage": {"text": "olha esse link https://x.com"}},
        }
    }
    msg = await adapter.receive_webhook(payload)
    assert msg.text == "olha esse link https://x.com"


async def test_evolution_receive_webhook_audio_sets_ref_without_downloading():
    adapter = EvolutionAdapter(base_url="http://evolution:8080", api_key="evo-key", instance="creative-ads")
    called = False

    async def _boom(file_ref):  # pragma: no cover - must never run
        nonlocal called
        called = True
        return b""

    adapter.download_media = _boom
    payload = {
        "data": {
            "key": {"remoteJid": "558599999999@s.whatsapp.net"},
            "message": {"audioMessage": {"url": "https://media/x.ogg"}},
        }
    }
    msg = await adapter.receive_webhook(payload)
    assert msg.audio_ref == "https://media/x.ogg"
    assert called is False


@respx.mock
async def test_evolution_download_media_posts():
    import base64 as _b64

    respx.post("http://evolution:8080/chat/getBase64FromMediaMessage/creative-ads").mock(
        return_value=Response(200, json={"base64": _b64.b64encode(b"audio").decode()})
    )
    adapter = EvolutionAdapter(base_url="http://evolution:8080", api_key="evo-key", instance="creative-ads")
    data = await adapter.download_media("https://media/x.ogg")
    assert data == b"audio"
    assert respx.calls.last.request.method == "POST"
