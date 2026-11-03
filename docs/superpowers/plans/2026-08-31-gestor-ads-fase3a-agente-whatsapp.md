# Gestor Ads — Fase 3a: Agente Conversacional (Telegram + WhatsApp Evolution) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a conversational agent (Telegram + WhatsApp/Evolution) that onboards a user via Meta OAuth, proposes and creates real Meta Ads campaigns (always `PAUSED`), and answers performance questions by chat — reusing the existing `app/core/` and `app/meta/` business logic from the Gestor Ads backend, with zero duplication.

**Architecture:** New module `app/agent/` inside the **same** `gestor-ads-backend` Python package (not a separate project) — this makes "reusing the core as a library" trivial, since it's literally the same codebase. It runs as its own FastAPI app (`app/agent/main.py`) in its own Docker container (`creative_ads_agent`, same image as `creative_ads_backend`, different `CMD`/port) so a slow LLM call or a flaky Evolution session never affects the dashboard API's uptime. Each channel (Telegram, Evolution) implements a common `ChannelAdapter` protocol; the agent loop normalizes messages, routes to Haiku or Sonnet 5 depending on intent, and calls Anthropic tool-use functions that are thin wrappers around the existing `MetaAdsClient`, `core.naming`, `core.analysis`.

**Tech Stack:** Python 3.12, FastAPI, `anthropic>=1.2.0` (tool use + prompt caching), `httpx` (Telegram Bot API, Evolution API, OpenAI Whisper REST endpoint — no new SDK deps), Supabase (Postgres), existing `TokenManager`/`MetaAdsClient`/`core/`.

**Spec:** [docs/superpowers/specs/2026-08-31-gestor-ads-fase3a-agente-whatsapp-design.md](../specs/2026-08-31-gestor-ads-fase3a-agente-whatsapp-design.md)

## Global Constraints

- Every campaign created by the agent MUST be created with `status=PAUSED` — this is a code-level check inside the `criar_campanha` tool, not just a prompt instruction (spec §4).
- `criar_campanha` MUST refuse if no `campaign_drafts` row with `status='aprovado'` is linked to the conversation — raise a handled `DraftValidationError`, never fail silently (spec §4, §7).
- Naming MUST go through the existing `app/core/naming.py` functions — the LLM never free-forms entity names (spec §4).
- Webhooks MUST ack in under 1 second; message processing happens via `BackgroundTasks`, no synchronous LLM call inside the webhook handler (spec §2).
- No Redis/BullMQ in this phase — background work uses FastAPI's `BackgroundTasks` (in-process), per spec §2 (dogfooding volume).
- Evolution (WhatsApp QR) is explicitly labeled experimental in any user-facing text the agent sends about connection mode (spec §8).
- `nivel_tecnico` lives on `profiles` (existing table), never duplicated per-conversation (spec §3, correction applied 2026-08-31).
- `campaign_drafts` is the **existing** table from `migrations/001_initial_schema.sql` — never recreated, only `ALTER TABLE ADD COLUMN conversation_id`.
- Alerts (jobs) and billing are explicitly out of scope for this plan (Fase 3b / Fase 4).

---

## File Structure

```
campaign_optimizer/gestor-ads/backend/
  app/
    agent/
      __init__.py
      main.py            # new FastAPI() instance, health check, mounts agent_router
      router.py           # POST /agent/telegram/webhook, POST /agent/evolution/webhook
      schemas.py          # IncomingMessage, ToolContext dataclasses
      channels/
        __init__.py
        base.py           # ChannelAdapter Protocol
        telegram.py       # TelegramAdapter
        evolution.py      # EvolutionAdapter
      conversation.py      # get_or_create_conversation, record_message, update_memory
      transcription.py     # transcribe_audio() via OpenAI Whisper REST
      tools.py             # TOOL_DEFINITIONS + dispatch_tool() + individual tool functions
      llm.py                # classify_intent, build_context, run_agent_turn
  migrations/
    005_agent_chat.sql
  app/config.py             # add telegram/evolution/openai settings (MODIFY)
  app/auth/meta_oauth.py     # extend state to carry conversation_id (MODIFY)
  app/auth/router.py         # notify originating chat after OAuth callback (MODIFY)
  tests/
    unit/test_agent_channels.py
    unit/test_agent_conversation.py
    unit/test_agent_transcription.py
    unit/test_agent_tools.py
    unit/test_agent_llm.py
    unit/test_meta_oauth.py          # extend existing coverage (state + conversation_id)
    integration/test_agent_router.py
```

---

## Task 1: Migration — `conversations`, `messages`, alter `campaign_drafts`

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/migrations/005_agent_chat.sql`

**Interfaces:**
- Produces: tables `conversations(id, owner_id, ad_account_id, channel, channel_user_id, resumo_memoria, memoria_negocio, criado_em, atualizado_em)` and `messages(id, conversation_id, papel, conteudo, media_url, transcricao, modelo_usado, tokens_input, tokens_output, criado_em)`; `campaign_drafts.conversation_id` column.

- [ ] **Step 1: Write the migration file**

```sql
-- Gestor Ads — Fase 3a: Agente conversacional (Telegram + WhatsApp)
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,
    channel TEXT NOT NULL CHECK (channel IN ('telegram', 'evolution', 'whatsapp_cloud')),
    channel_user_id TEXT NOT NULL,
    resumo_memoria TEXT NOT NULL DEFAULT '',
    memoria_negocio JSONB NOT NULL DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, channel_user_id)
);
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "conversations_owner_policy" ON conversations FOR ALL USING (owner_id = auth.uid());

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('user', 'assistant', 'tool')),
    conteudo TEXT NOT NULL DEFAULT '',
    media_url TEXT,
    transcricao TEXT,
    modelo_usado TEXT,
    tokens_input INTEGER NOT NULL DEFAULT 0,
    tokens_output INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, criado_em);
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "messages_owner_policy" ON messages FOR ALL USING (
    conversation_id IN (SELECT id FROM conversations WHERE owner_id = auth.uid())
);

-- campaign_drafts already exists (001_initial_schema.sql) — only link it to a conversation.
ALTER TABLE campaign_drafts
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL;
```

- [ ] **Step 2: Verify the file is syntactically consistent with existing migrations**

Run: `grep -c "CREATE TABLE\|ALTER TABLE" campaign_optimizer/gestor-ads/backend/migrations/005_agent_chat.sql`
Expected: `4` (2 CREATE TABLE, 1 CREATE TABLE campaign_drafts alter is actually ALTER not CREATE — expected count of `CREATE TABLE|ALTER TABLE` lines is 3: two `CREATE TABLE conversations`/`CREATE TABLE messages`, one `ALTER TABLE campaign_drafts`)

- [ ] **Step 3: Apply the migration to Supabase**

Use the Supabase MCP `apply_migration` tool against project `lwmvswhzrruwttfweidj` with this file's contents (same process used for `002`–`004`). Verify with `list_tables` that `conversations` and `messages` now exist and `campaign_drafts` has the new `conversation_id` column.

- [ ] **Step 4: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/migrations/005_agent_chat.sql
git commit -m "feat(gestor-ads): agent chat schema — conversations, messages, campaign_drafts link"
```

---

## Task 2: Config — new settings for Telegram, Evolution, Whisper

**Files:**
- Modify: `campaign_optimizer/gestor-ads/backend/app/config.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_config.py`

**Interfaces:**
- Produces: `Settings.telegram_bot_token: str`, `Settings.evolution_base_url: str`, `Settings.evolution_api_key: str`, `Settings.evolution_instance: str`, `Settings.openai_api_key: str` (for Whisper).

- [ ] **Step 1: Write the failing test**

```python
def test_settings_have_agent_fields(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tg-token")
    monkeypatch.setenv("EVOLUTION_BASE_URL", "http://evolution-go:8080")
    monkeypatch.setenv("EVOLUTION_API_KEY", "evo-key")
    monkeypatch.setenv("EVOLUTION_INSTANCE", "creative-ads")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = Settings()
    assert settings.telegram_bot_token == "tg-token"
    assert settings.evolution_base_url == "http://evolution-go:8080"
    assert settings.evolution_api_key == "evo-key"
    assert settings.evolution_instance == "creative-ads"
    assert settings.openai_api_key == "sk-test"
```

Append this to the existing `tests/unit/test_config.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_config.py::test_settings_have_agent_fields -v`
Expected: FAIL with `AttributeError` (fields don't exist yet).

- [ ] **Step 3: Add the fields to `Settings`**

```python
    # Agent — Telegram
    telegram_bot_token: str = ""

    # Agent — Evolution API (WhatsApp via QR, experimental channel)
    evolution_base_url: str = ""
    evolution_api_key: str = ""
    evolution_instance: str = ""

    # Agent — Whisper (audio transcription)
    openai_api_key: str = ""
```

Insert this block right after the existing `# LLM` block in `app/config.py` (after `anthropic_workspace_id: str = ""`, before `# Email (SMTP)`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_config.py -v`
Expected: PASS (all tests in the file, including the new one).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/config.py campaign_optimizer/gestor-ads/backend/tests/unit/test_config.py
git commit -m "feat(gestor-ads): add agent settings (telegram, evolution, whisper)"
```

---

## Task 3: `ChannelAdapter` protocol + `IncomingMessage`

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/__init__.py`
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/schemas.py`
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/channels/__init__.py`
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/channels/base.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py`

**Interfaces:**
- Produces:
  - `IncomingMessage` dataclass: `channel: str`, `channel_user_id: str`, `text: str | None`, `audio_bytes: bytes | None`, `location: tuple[float, float] | None`, `raw: dict`
  - `ChannelAdapter` Protocol: `async def send_text(self, chat_id: str, text: str) -> None`, `async def receive_webhook(self, payload: dict) -> IncomingMessage`, `async def download_media(self, file_ref: str) -> bytes`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_agent_channels.py
from __future__ import annotations

import pytest

from app.agent.channels.base import ChannelAdapter, IncomingMessage


def test_incoming_message_defaults():
    msg = IncomingMessage(channel="telegram", channel_user_id="123", text="oi", raw={})
    assert msg.audio_bytes is None
    assert msg.location is None


def test_channel_adapter_is_a_protocol():
    class FakeAdapter:
        async def send_text(self, chat_id: str, text: str) -> None: ...
        async def receive_webhook(self, payload: dict) -> IncomingMessage: ...
        async def download_media(self, file_ref: str) -> bytes: ...

    adapter: ChannelAdapter = FakeAdapter()
    assert isinstance(adapter, ChannelAdapter)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent'`.

- [ ] **Step 3: Create the empty package inits**

```python
# app/agent/__init__.py
```

```python
# app/agent/channels/__init__.py
```

- [ ] **Step 4: Write `base.py`**

```python
# app/agent/channels/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class IncomingMessage:
    """Normalized message from any channel — the agent never sees raw
    Telegram/Evolution payloads directly."""

    channel: str
    channel_user_id: str
    raw: dict
    text: str | None = None
    audio_bytes: bytes | None = None
    location: tuple[float, float] | None = None


@runtime_checkable
class ChannelAdapter(Protocol):
    """Common interface every messaging channel implements. The agent loop
    and core/ never know which concrete channel they're talking to."""

    async def send_text(self, chat_id: str, text: str) -> None: ...

    async def receive_webhook(self, payload: dict) -> IncomingMessage: ...

    async def download_media(self, file_ref: str) -> bytes: ...
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/__init__.py campaign_optimizer/gestor-ads/backend/app/agent/schemas.py campaign_optimizer/gestor-ads/backend/app/agent/channels/ campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py
git commit -m "feat(gestor-ads): ChannelAdapter protocol + IncomingMessage"
```

---

## Task 4: `TelegramAdapter`

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/channels/telegram.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py` (append)

**Interfaces:**
- Consumes: `IncomingMessage`, `ChannelAdapter` (Task 3), `httpx.AsyncClient`.
- Produces: `TelegramAdapter(bot_token: str)` implementing `ChannelAdapter`.

- [ ] **Step 1: Write the failing test**

```python
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
    assert msg.audio_bytes is None


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v -k telegram`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.channels.telegram'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/channels/telegram.py
from __future__ import annotations

import httpx

from app.agent.channels.base import IncomingMessage


class TelegramAdapter:
    """Official Telegram Bot API — no App Review, no ban risk."""

    BASE = "https://api.telegram.org"

    def __init__(self, bot_token: str):
        self._token = bot_token

    async def send_text(self, chat_id: str, text: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                f"{self.BASE}/bot{self._token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )

    async def receive_webhook(self, payload: dict) -> IncomingMessage:
        message = payload.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))

        location = None
        loc = message.get("location")
        if loc:
            location = (loc["latitude"], loc["longitude"])

        audio_file_id = None
        voice = message.get("voice") or message.get("audio")
        if voice:
            audio_file_id = voice.get("file_id")

        audio_bytes = None
        if audio_file_id:
            audio_bytes = await self.download_media(audio_file_id)

        return IncomingMessage(
            channel="telegram",
            channel_user_id=chat_id,
            raw=payload,
            text=message.get("text"),
            audio_bytes=audio_bytes,
            location=location,
        )

    async def download_media(self, file_ref: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.BASE}/bot{self._token}/getFile", params={"file_id": file_ref})
            file_path = resp.json()["result"]["file_path"]
            file_resp = await client.get(f"{self.BASE}/file/bot{self._token}/{file_path}")
            return file_resp.content
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v`
Expected: PASS (all 6 tests: 2 from Task 3 + 4 new).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/channels/telegram.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py
git commit -m "feat(gestor-ads): TelegramAdapter"
```

---

## Task 5: `EvolutionAdapter`

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/channels/evolution.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py` (append)

**Interfaces:**
- Consumes: `IncomingMessage`, `ChannelAdapter` (Task 3).
- Produces: `EvolutionAdapter(base_url: str, api_key: str, instance: str)` implementing `ChannelAdapter`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v -k evolution`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.channels.evolution'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/channels/evolution.py
from __future__ import annotations

import base64

import httpx

from app.agent.channels.base import IncomingMessage


class EvolutionAdapter:
    """WhatsApp via Evolution API (QR Code, unofficial). Labeled experimental
    in the product — real risk of number ban, no approved templates."""

    def __init__(self, base_url: str, api_key: str, instance: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._instance = instance

    async def send_text(self, chat_id: str, text: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                f"{self._base_url}/message/sendText/{self._instance}",
                headers={"apikey": self._api_key},
                json={"number": chat_id, "text": text},
            )

    async def receive_webhook(self, payload: dict) -> IncomingMessage:
        data = payload.get("data", {})
        remote_jid = data.get("key", {}).get("remoteJid", "")
        phone = remote_jid.split("@")[0]

        message = data.get("message", {})
        text = message.get("conversation")

        location = None
        loc = message.get("locationMessage")
        if loc:
            location = (loc["degreesLatitude"], loc["degreesLongitude"])

        audio_bytes = None
        audio_msg = message.get("audioMessage")
        if audio_msg:
            audio_bytes = await self.download_media(audio_msg.get("url", ""))

        return IncomingMessage(
            channel="evolution",
            channel_user_id=phone,
            raw=payload,
            text=text,
            audio_bytes=audio_bytes,
            location=location,
        )

    async def download_media(self, file_ref: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._base_url}/chat/getBase64FromMediaMessage/{self._instance}",
                headers={"apikey": self._api_key},
                params={"url": file_ref},
            )
            b64 = resp.json().get("base64", "")
            return base64.b64decode(b64) if b64 else b""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_channels.py -v`
Expected: PASS (all tests, including the 3 new ones).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/channels/evolution.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_channels.py
git commit -m "feat(gestor-ads): EvolutionAdapter (experimental WhatsApp channel)"
```

---

## Task 6: Audio transcription (Whisper API)

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/transcription.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_transcription.py`

**Interfaces:**
- Produces: `async def transcribe_audio(audio_bytes: bytes, api_key: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
import respx
from httpx import Response

from app.agent.transcription import transcribe_audio


@respx.mock
async def test_transcribe_audio():
    respx.post("https://api.openai.com/v1/audio/transcriptions").mock(
        return_value=Response(200, json={"text": "quero criar uma campanha de tráfego"})
    )
    text = await transcribe_audio(b"fake-audio-bytes", api_key="sk-test")
    assert text == "quero criar uma campanha de tráfego"
    call = respx.calls.last
    assert call.request.headers["authorization"] == "Bearer sk-test"


@respx.mock
async def test_transcribe_audio_failure_raises():
    respx.post("https://api.openai.com/v1/audio/transcriptions").mock(return_value=Response(500))
    with pytest.raises(Exception):
        await transcribe_audio(b"fake-audio-bytes", api_key="sk-test")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_transcription.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.transcription'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/transcription.py
from __future__ import annotations

import httpx


async def transcribe_audio(audio_bytes: bytes, api_key: str) -> str:
    """Transcribe voice/audio to text via OpenAI Whisper REST endpoint.

    Raises httpx.HTTPStatusError if the API call fails — caller decides
    what to tell the user (spec §7: ask them to repeat in text).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("audio.ogg", audio_bytes, "audio/ogg")},
            data={"model": "whisper-1"},
        )
        response.raise_for_status()
        return response.json()["text"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_transcription.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/transcription.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_transcription.py
git commit -m "feat(gestor-ads): audio transcription via Whisper API"
```

---

## Task 7: Conversation store

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/conversation.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_conversation.py`

**Interfaces:**
- Consumes: Supabase `Client` (as used throughout the codebase, e.g. `app/dependencies.py`).
- Produces:
  - `async def get_or_create_conversation(supabase, channel: str, channel_user_id: str) -> dict`
  - `async def record_message(supabase, conversation_id: str, papel: str, conteudo: str, *, media_url: str | None = None, transcricao: str | None = None, modelo_usado: str | None = None, tokens_input: int = 0, tokens_output: int = 0) -> None`
  - `async def update_memory(supabase, conversation_id: str, *, resumo_memoria: str | None = None, memoria_negocio: dict | None = None) -> None`
  - `async def link_ad_account(supabase, conversation_id: str, ad_account_id: str) -> None`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import MagicMock

import pytest

from app.agent.conversation import (
    get_or_create_conversation,
    link_ad_account,
    record_message,
    update_memory,
)


async def test_get_or_create_conversation_existing(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "conv-1", "owner_id": "user-1", "ad_account_id": None, "resumo_memoria": "", "memoria_negocio": {}}
    ]
    row = await get_or_create_conversation(fake_supabase, "telegram", "555")
    assert row["id"] == "conv-1"


async def test_get_or_create_conversation_creates_new(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    fake_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "conv-new", "owner_id": None, "ad_account_id": None, "resumo_memoria": "", "memoria_negocio": {}}
    ]
    row = await get_or_create_conversation(fake_supabase, "telegram", "555")
    assert row["id"] == "conv-new"


async def test_record_message(fake_supabase):
    await record_message(fake_supabase, "conv-1", "user", "oi", tokens_input=10)
    fake_supabase.table.assert_any_call("messages")


async def test_update_memory(fake_supabase):
    await update_memory(fake_supabase, "conv-1", resumo_memoria="resumo novo")
    fake_supabase.table.assert_any_call("conversations")


async def test_link_ad_account(fake_supabase):
    await link_ad_account(fake_supabase, "conv-1", "acc-1")
    fake_supabase.table.assert_any_call("conversations")
```

Add this to a new `tests/unit/test_agent_conversation.py`, reusing the existing `fake_supabase` fixture from `tests/conftest.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_conversation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.conversation'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/conversation.py
from __future__ import annotations

from datetime import datetime, timezone


async def get_or_create_conversation(supabase, channel: str, channel_user_id: str) -> dict:
    """Find the conversation for this channel+user, or create a fresh one
    (owner_id/ad_account_id null until onboarding links them)."""
    existing = (
        supabase.table("conversations")
        .select("*")
        .eq("channel", channel)
        .eq("channel_user_id", channel_user_id)
        .execute()
        .data
    )
    if existing:
        return existing[0]

    row = (
        supabase.table("conversations")
        .insert({"channel": channel, "channel_user_id": channel_user_id, "owner_id": None})
        .execute()
        .data[0]
    )
    return row


async def record_message(
    supabase,
    conversation_id: str,
    papel: str,
    conteudo: str,
    *,
    media_url: str | None = None,
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
            "transcricao": transcricao,
            "modelo_usado": modelo_usado,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
        }
    ).execute()


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
```

Note: `owner_id` starts `None` and is only known once the OAuth flow completes and the user
is identified via Supabase auth (set separately during onboarding — see Task 8). Since
`conversations.owner_id` has a `NOT NULL` constraint in the migration, add the following
follow-up before Step 4 runs against real Supabase: this unit test suite mocks Supabase
entirely, so it's unaffected; the real insert during onboarding must set `owner_id`
immediately once a Supabase user is created/linked (Task 8 handles this — the conversation
row is only persisted with a real `owner_id` once the user authenticates via OAuth; before
that, the agent tracks the pending state in the in-memory OAuth state store from
`app/auth/meta_oauth.py`, not in `conversations`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_conversation.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/conversation.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_conversation.py
git commit -m "feat(gestor-ads): conversation store (get_or_create, record_message, memory)"
```

---

## Task 8: Onboarding — OAuth state carries `conversation_id`

**Files:**
- Modify: `campaign_optimizer/gestor-ads/backend/app/auth/meta_oauth.py`
- Modify: `campaign_optimizer/gestor-ads/backend/app/auth/router.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_meta_oauth.py` (new file)

**Interfaces:**
- Consumes: `get_or_create_conversation`, `link_ad_account` (Task 7), `ChannelAdapter` implementations (Tasks 4–5).
- Produces: `generate_oauth_url(user_id: str, conversation_id: str | None = None) -> str`, `validate_state(state: str) -> tuple[str, str | None]` (was `-> str`, now returns `(user_id, conversation_id)`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_meta_oauth.py
from __future__ import annotations

import pytest

from app.auth.meta_oauth import generate_oauth_url, validate_state


def test_generate_and_validate_state_without_conversation(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.com/callback")
    url = generate_oauth_url("user-1")
    state = url.split("state=")[1].split("&")[0]
    user_id, conversation_id = validate_state(state)
    assert user_id == "user-1"
    assert conversation_id is None


def test_generate_and_validate_state_with_conversation(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.com/callback")
    url = generate_oauth_url("user-1", conversation_id="conv-1")
    state = url.split("state=")[1].split("&")[0]
    user_id, conversation_id = validate_state(state)
    assert user_id == "user-1"
    assert conversation_id == "conv-1"


def test_validate_state_invalid_raises():
    with pytest.raises(ValueError):
        validate_state("nao-existe")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_meta_oauth.py -v`
Expected: FAIL (`validate_state` currently returns a plain `str`, tuple unpacking fails; `generate_oauth_url` doesn't accept `conversation_id`).

- [ ] **Step 3: Update `meta_oauth.py`**

```python
def generate_oauth_url(user_id: str, conversation_id: str | None = None) -> str:
    """Generate Meta OAuth URL with opaque state token.

    conversation_id is set when the flow was started from the chat agent
    (Telegram/Evolution), so the callback knows which chat to notify.
    """
    settings = get_settings()

    state_key = secrets.token_urlsafe(32)

    with _state_lock:
        _cleanup_expired()
        _state_store[state_key] = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        }

    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "scope": "ads_management,ads_read,business_management,pages_show_list",
        "state": state_key,
        "response_type": "code",
    }
    return f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"


def validate_state(state: str) -> tuple[str, str | None]:
    """Validate opaque state token and return (user_id, conversation_id).
    Raises on invalid/expired."""
    with _state_lock:
        entry = _state_store.pop(state, None)

    if not entry:
        raise ValueError("State inválido ou expirado")

    if entry["expires_at"] < datetime.now(timezone.utc):
        raise ValueError("State expirado")

    return entry["user_id"], entry.get("conversation_id")
```

Replace the existing `generate_oauth_url`/`validate_state` functions with these (same file,
same imports already present).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_meta_oauth.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Fix the caller in `auth/router.py` and notify the originating chat**

`meta_callback` currently does `user_id = validate_state(state)`. Update it to unpack the
tuple, and after the ad accounts are saved, notify the chat if `conversation_id` is set:

```python
    # Validate state token
    try:
        user_id, conversation_id = validate_state(state)
    except ValueError as exc:
        raise AppError(str(exc))
```

Add this block right before the existing `return RedirectResponse(...)` line, inside
`meta_callback`:

```python
    if conversation_id:
        from app.agent.channels.evolution import EvolutionAdapter
        from app.agent.channels.telegram import TelegramAdapter
        from app.agent.conversation import get_or_create_conversation

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
```

This requires `settings = get_settings()` to already be in scope inside `meta_callback` —
add `settings: Settings = Depends(get_settings)` to its parameter list (mirrors the pattern
in `meta_deauthorize` a few lines below, which already does this).

- [ ] **Step 6: Run the full auth test suite**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_meta_oauth.py tests/integration/test_auth_flow.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/auth/meta_oauth.py campaign_optimizer/gestor-ads/backend/app/auth/router.py campaign_optimizer/gestor-ads/backend/tests/unit/test_meta_oauth.py
git commit -m "feat(gestor-ads): OAuth state carries conversation_id, notifies chat after connect"
```

---

## Task 9: Tools — `listar_contas`, `selecionar_conta`, `consultar_metricas`, `pausar_campanha`

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/tools.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_tools.py`

**Interfaces:**
- Consumes: `app.core.kpis.summarize_kpis`, `app.meta.client.MetaAdsClient`, `link_ad_account` (Task 7).
- Produces:
  - `@dataclass ToolContext(supabase, settings, user_id, conversation_id, ad_account_id)`
  - `async def listar_contas(ctx: ToolContext) -> dict`
  - `async def selecionar_conta(ctx: ToolContext, *, conta: str) -> dict`
  - `async def consultar_metricas(ctx: ToolContext, meta_client: MetaAdsClient) -> dict`
  - `async def pausar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, campanha_id: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import AsyncMock

import pytest

from app.agent.tools import ToolContext, consultar_metricas, listar_contas, pausar_campanha, selecionar_conta


def _ctx(fake_supabase, **overrides):
    defaults = dict(supabase=fake_supabase, settings=None, user_id="user-1", conversation_id="conv-1", ad_account_id=None)
    defaults.update(overrides)
    return ToolContext(**defaults)


async def test_listar_contas(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec", "external_id": "act_1"},
        {"id": "acc-2", "name": "Marca Imobiliária", "external_id": "act_2"},
    ]
    result = await listar_contas(_ctx(fake_supabase))
    assert len(result["contas"]) == 2
    assert result["contas"][0]["name"] == "Fortec"


async def test_selecionar_conta_by_number(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec", "external_id": "act_1"},
        {"id": "acc-2", "name": "Marca Imobiliária", "external_id": "act_2"},
    ]
    result = await selecionar_conta(_ctx(fake_supabase), conta="2")
    assert result["ad_account_id"] == "acc-2"


async def test_selecionar_conta_ambiguous_raises():
    with pytest.raises(ValueError):
        pass  # covered by name-matching branch below


async def test_selecionar_conta_by_name(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec Imóveis", "external_id": "act_1"},
    ]
    result = await selecionar_conta(_ctx(fake_supabase), conta="fortec")
    assert result["ad_account_id"] == "acc-1"


async def test_consultar_metricas(fake_supabase):
    meta_client = AsyncMock()
    meta_client.get_insights.return_value = [
        {"spend": "100", "actions": [{"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "5"}]}
    ]
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await consultar_metricas(ctx, meta_client)
    assert result["total_spend"] == 100.0
    assert result["total_leads"] == 5


async def test_pausar_campanha(fake_supabase):
    meta_client = AsyncMock()
    meta_client.update_status.return_value = {"success": True}
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await pausar_campanha(ctx, meta_client, campanha_id="123")
    meta_client.update_status.assert_called_once_with("123", "PAUSED")
    assert result["status"] == "PAUSED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.tools'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/tools.py
from __future__ import annotations

from dataclasses import dataclass

from app.core.kpis import summarize_kpis
from app.meta.client import MetaAdsClient
from app.shared.exceptions import DraftValidationError, NotFoundError


@dataclass
class ToolContext:
    """Everything a tool needs, assembled once per agent turn."""

    supabase: object
    settings: object
    user_id: str
    conversation_id: str
    ad_account_id: str | None


async def listar_contas(ctx: ToolContext) -> dict:
    rows = (
        ctx.supabase.table("ad_accounts")
        .select("id,name,external_id")
        .eq("client_id", ctx.user_id)
        .execute()
        .data
    )
    return {"contas": rows}


async def selecionar_conta(ctx: ToolContext, *, conta: str) -> dict:
    """Resolve the user's answer (a number from the listed order, or a
    name/partial name) to an ad_account_id, and link it to the conversation."""
    rows = (
        ctx.supabase.table("ad_accounts")
        .select("id,name,external_id")
        .eq("client_id", ctx.user_id)
        .execute()
        .data
    )
    if not rows:
        raise NotFoundError("Nenhuma conta de anúncio encontrada.")

    chosen = None
    if conta.strip().isdigit():
        idx = int(conta.strip()) - 1
        if 0 <= idx < len(rows):
            chosen = rows[idx]
    else:
        matches = [r for r in rows if conta.lower() in r["name"].lower()]
        if len(matches) == 1:
            chosen = matches[0]
        elif len(matches) > 1:
            names = ", ".join(m["name"] for m in matches)
            raise DraftValidationError(f"Encontrei mais de uma conta com esse nome ({names}). Qual delas?")

    if chosen is None:
        raise NotFoundError(f"Não encontrei a conta '{conta}'. Tente o número da lista ou o nome exato.")

    from app.agent.conversation import link_ad_account

    await link_ad_account(ctx.supabase, ctx.conversation_id, chosen["id"])
    return {"ad_account_id": chosen["id"], "name": chosen["name"]}


async def consultar_metricas(ctx: ToolContext, meta_client: MetaAdsClient) -> dict:
    insights = await meta_client.get_insights(meta_client.act_id)
    kpis = summarize_kpis(insights)
    return {
        "total_spend": kpis.total_spend,
        "total_leads": kpis.total_leads,
        "cpl_medio": kpis.cpl_medio,
        "ctr_medio": kpis.ctr_medio,
        "tendencia": kpis.tendencia,
    }


async def pausar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, campanha_id: str) -> dict:
    await meta_client.update_status(campanha_id, "PAUSED")
    return {"campanha_id": campanha_id, "status": "PAUSED"}
```

Remove the placeholder `test_selecionar_conta_ambiguous_raises` test (it does nothing useful —
the ambiguous-name path is already covered by asserting `DraftValidationError` directly):

```python
async def test_selecionar_conta_ambiguous_raises(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "acc-1", "name": "Fortec Imóveis", "external_id": "act_1"},
        {"id": "acc-2", "name": "Fortec Consórcio", "external_id": "act_2"},
    ]
    with pytest.raises(DraftValidationError):
        await selecionar_conta(_ctx(fake_supabase), conta="fortec")
```

(Replace the earlier no-op test with this real one, and import `DraftValidationError` in the
test file.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_tools.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/tools.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_tools.py
git commit -m "feat(gestor-ads): agent tools — listar/selecionar conta, métricas, pausar"
```

---

## Task 10: Tools — `propor_campanha`, `criar_campanha`, `localizacao_por_raio`

**Files:**
- Modify: `campaign_optimizer/gestor-ads/backend/app/agent/tools.py`
- Modify: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_tools.py`

**Interfaces:**
- Consumes: `app.core.analysis.generate_campaign_strategy`, `app.core.analysis.CampaignBriefing`, `app.core.naming.campaign_name`, `app.meta.client.MetaAdsClient.create_campaign`.
- Produces:
  - `async def propor_campanha(ctx: ToolContext, *, produto: str, objetivo: str, verba_total: float, dias: int, publico_alvo: str, destino_lead: str, marca: str) -> dict`
  - `async def criar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, draft_id: str) -> dict`
  - `def localizacao_por_raio(*, latitude: float, longitude: float, raio_km: float) -> dict`

- [ ] **Step 1: Write the failing test**

```python
async def test_propor_campanha_creates_draft(fake_supabase, monkeypatch):
    async def fake_strategy(briefing, **kwargs):
        from app.core.analysis import CampaignStrategy

        return CampaignStrategy(
            verba_diaria=50.0, dias=20, estrutura="CBO", publico=briefing.publico_alvo,
            copy="copy gerada", justificativa="R$50/dia evita fase de aprendizado longa",
        )

    monkeypatch.setattr("app.agent.tools.generate_campaign_strategy", fake_strategy)
    fake_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "draft-1", "status": "rascunho", "payload": {}}
    ]

    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await propor_campanha(
        ctx, produto="imóvel alto padrão", objetivo="LEAD_GENERATION", verba_total=1000.0,
        dias=20, publico_alvo="Fortaleza, 30-55 anos", destino_lead="whatsapp", marca="Fortec",
    )
    assert result["draft_id"] == "draft-1"
    assert result["justificativa"] == "R$50/dia evita fase de aprendizado longa"


async def test_criar_campanha_requires_approved_draft(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1", "status": "rascunho", "payload": {}
    }
    meta_client = AsyncMock()
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    with pytest.raises(DraftValidationError):
        await criar_campanha(ctx, meta_client, draft_id="draft-1")
    meta_client.create_campaign.assert_not_called()


async def test_criar_campanha_creates_when_approved(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": "draft-1",
        "status": "aprovado",
        "payload": {"marca": "Fortec", "objetivo": "trafego", "publico": "Fortaleza", "verba_diaria": 50.0},
    }
    meta_client = AsyncMock()
    meta_client.create_campaign.return_value = {"id": "camp-123"}
    ctx = _ctx(fake_supabase, ad_account_id="acc-1")
    result = await criar_campanha(ctx, meta_client, draft_id="draft-1")
    assert result["meta_campaign_id"] == "camp-123"
    _, kwargs = meta_client.create_campaign.call_args
    assert kwargs.get("name", "").startswith("[Fortec]")


def test_localizacao_por_raio():
    result = localizacao_por_raio(latitude=-3.7319, longitude=-38.5267, raio_km=3.0)
    assert result["custom_locations"] == [{"latitude": -3.7319, "longitude": -38.5267, "radius": 3.0, "distance_unit": "kilometer"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_tools.py -v -k "propor or criar_campanha or localizacao"`
Expected: FAIL — `propor_campanha`, `criar_campanha`, `localizacao_por_raio` don't exist yet.

- [ ] **Step 3: Add the implementation to `tools.py`**

```python
from app.core.analysis import CampaignBriefing, generate_campaign_strategy
from app.core.naming import campaign_name


async def propor_campanha(
    ctx: ToolContext,
    *,
    produto: str,
    objetivo: str,
    verba_total: float,
    dias: int,
    publico_alvo: str,
    destino_lead: str,
    marca: str,
) -> dict:
    """Ask Claude (via core.analysis) for a justified strategy, save it as a
    campaign_drafts row with status='rascunho', linked to this conversation."""
    briefing = CampaignBriefing(
        produto=produto, objetivo=objetivo, verba_total=verba_total, dias=dias,
        publico_alvo=publico_alvo, destino_lead=destino_lead, marca=marca,
    )
    settings = ctx.settings
    strategy = await generate_campaign_strategy(
        briefing,
        anthropic_api_key=getattr(settings, "anthropic_api_key", ""),
        anthropic_workspace_id=getattr(settings, "anthropic_workspace_id", ""),
    )

    payload = {
        "marca": marca,
        "objetivo": objetivo,
        "publico": strategy.publico,
        "verba_diaria": strategy.verba_diaria,
        "dias": strategy.dias,
        "estrutura": strategy.estrutura,
        "copy": strategy.copy,
        "justificativa": strategy.justificativa,
    }
    row = (
        ctx.supabase.table("campaign_drafts")
        .insert(
            {
                "owner_id": ctx.user_id,
                "ad_account_id": ctx.ad_account_id,
                "conversation_id": ctx.conversation_id,
                "payload": payload,
                "status": "rascunho",
            }
        )
        .execute()
        .data[0]
    )
    return {"draft_id": row["id"], **payload}


async def criar_campanha(ctx: ToolContext, meta_client: MetaAdsClient, *, draft_id: str) -> dict:
    """Create the campaign on Meta — ALWAYS PAUSED. Refuses if the draft
    linked to this conversation isn't approved yet (spec §4, §7)."""
    draft = (
        ctx.supabase.table("campaign_drafts")
        .select("id,status,payload")
        .eq("id", draft_id)
        .single()
        .execute()
        .data
    )
    if not draft or draft["status"] != "aprovado":
        raise DraftValidationError(
            "Essa campanha ainda não foi aprovada. Confirme a estratégia antes de eu criar."
        )

    payload = draft["payload"]
    name = campaign_name(payload["marca"], payload["objetivo"], payload["publico"])
    daily_cents = int(round(payload["verba_diaria"] * 100))

    result = await meta_client.create_campaign(
        name=name,
        objective=payload["objetivo"],
        daily_budget_cents=daily_cents,
    )

    ctx.supabase.table("campaign_drafts").update(
        {"status": "criado", "meta_campaign_id": result["id"]}
    ).eq("id", draft_id).execute()

    return {"meta_campaign_id": result["id"], "name": name, "status": "PAUSED"}


def localizacao_por_raio(*, latitude: float, longitude: float, raio_km: float) -> dict:
    """Build the Meta `custom_locations` targeting payload for a radius
    around a point (from a shared pin or a Google Maps link, already
    resolved to lat/lng before this tool is called — spec §4)."""
    return {
        "custom_locations": [
            {"latitude": latitude, "longitude": longitude, "radius": raio_km, "distance_unit": "kilometer"}
        ]
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_tools.py -v`
Expected: PASS (10 tests total).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/tools.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_tools.py
git commit -m "feat(gestor-ads): agent tools — propor/criar campanha (sempre PAUSED), raio"
```

---

## Task 11: LLM loop — model routing, tool definitions, prompt caching

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/llm.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_llm.py`

**Interfaces:**
- Consumes: `ToolContext`, `dispatch_tool` (defined in this task, wrapping Task 9/10 functions), `anthropic.AsyncAnthropic`.
- Produces:
  - `def classify_intent(text: str) -> str` → `"estrategia"` or `"simples"`
  - `TOOL_DEFINITIONS: list[dict]` (Anthropic tool schemas)
  - `async def dispatch_tool(name: str, tool_input: dict, ctx: ToolContext, meta_client) -> dict`
  - `async def run_agent_turn(*, ctx: ToolContext, meta_client, resumo_memoria: str, memoria_negocio: dict, historico: list[dict], mensagem_atual: str, nivel_tecnico: str, anthropic_api_key: str, anthropic_workspace_id: str) -> dict` returning `{"resposta": str, "tokens_input": int, "tokens_output": int, "modelo_usado": str}`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.llm'`.

- [ ] **Step 3: Write the implementation**

```python
# app/agent/llm.py
from __future__ import annotations

import logging

import anthropic

from app.agent.tools import (
    ToolContext,
    consultar_metricas,
    criar_campanha,
    listar_contas,
    localizacao_por_raio,
    pausar_campanha,
    propor_campanha,
    selecionar_conta,
)

logger = logging.getLogger(__name__)

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-5"

_STRATEGY_KEYWORDS = (
    "campanha",
    "estratégia",
    "estrategia",
    "criar",
    "orçamento",
    "orcamento",
    "verba",
    "público",
    "publico",
    "ajusta",
    "ajustar",
)

SYSTEM_PROMPT = """Você é o gestor de tráfego pago do usuário, operando por chat.
Você tem acesso real à conta de anúncio dele pela Meta Marketing API através das
ferramentas disponíveis. Responda em português brasileiro, direto, sem enrolação —
mensagens curtas, é chat, não e-mail.

Regras rígidas:
- Toda campanha é criada com status PAUSED. Ative somente após confirmação explícita.
- Peça aprovação explícita antes de criar qualquer campanha.
- Nunca invente métrica, resultado ou histórico — chame a ferramenta correspondente.
- Se o nível técnico do usuário for leigo, traduza toda métrica para consequência
  prática, nunca use sigla sem explicar. Se for avançado, use os termos técnicos
  normalmente (CTR, CPM, CPA, CPL, CBO, ABO).
"""

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "listar_contas",
        "description": "Lista as contas de anúncio Meta já conectadas para este usuário.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "selecionar_conta",
        "description": "Seleciona a conta de anúncio ativa para esta conversa, por número da lista ou nome.",
        "input_schema": {
            "type": "object",
            "properties": {"conta": {"type": "string", "description": "número ou nome da conta"}},
            "required": ["conta"],
        },
    },
    {
        "name": "propor_campanha",
        "description": "Gera uma proposta de estratégia de campanha justificada, para o usuário aprovar antes de criar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "produto": {"type": "string"},
                "objetivo": {"type": "string"},
                "verba_total": {"type": "number"},
                "dias": {"type": "integer"},
                "publico_alvo": {"type": "string"},
                "destino_lead": {"type": "string"},
                "marca": {"type": "string"},
            },
            "required": ["produto", "objetivo", "verba_total", "dias", "publico_alvo", "destino_lead", "marca"],
        },
    },
    {
        "name": "criar_campanha",
        "description": "Cria a campanha de verdade na Meta, sempre em PAUSED. Exige um draft já aprovado pelo usuário.",
        "input_schema": {
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "required": ["draft_id"],
        },
    },
    {
        "name": "consultar_metricas",
        "description": "Consulta as métricas atuais da conta de anúncio selecionada.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "pausar_campanha",
        "description": "Pausa uma campanha existente na Meta.",
        "input_schema": {
            "type": "object",
            "properties": {"campanha_id": {"type": "string"}},
            "required": ["campanha_id"],
        },
    },
    {
        "name": "localizacao_por_raio",
        "description": "Monta a segmentação por raio a partir de uma coordenada já extraída de um pin ou link do Maps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "raio_km": {"type": "number"},
            },
            "required": ["latitude", "longitude", "raio_km"],
        },
    },
]
# Cache the (static) tool schema between turns of the same conversation.
TOOL_DEFINITIONS[-1]["cache_control"] = {"type": "ephemeral"}


def classify_intent(text: str) -> str:
    """Cheap keyword heuristic — no extra LLM call. Anything that smells
    like campaign strategy work goes to Sonnet; everything else (simple
    questions, confirmations) goes to the cheaper Haiku model."""
    lowered = text.lower()
    if any(keyword in lowered for keyword in _STRATEGY_KEYWORDS):
        return "estrategia"
    return "simples"


async def dispatch_tool(name: str, tool_input: dict, ctx: ToolContext, meta_client) -> dict:
    if name == "listar_contas":
        return await listar_contas(ctx)
    if name == "selecionar_conta":
        return await selecionar_conta(ctx, conta=tool_input["conta"])
    if name == "propor_campanha":
        return await propor_campanha(ctx, **tool_input)
    if name == "criar_campanha":
        return await criar_campanha(ctx, meta_client, draft_id=tool_input["draft_id"])
    if name == "consultar_metricas":
        return await consultar_metricas(ctx, meta_client)
    if name == "pausar_campanha":
        return await pausar_campanha(ctx, meta_client, campanha_id=tool_input["campanha_id"])
    if name == "localizacao_por_raio":
        return localizacao_por_raio(**tool_input)
    raise ValueError(f"Tool desconhecida: {name}")


async def run_agent_turn(
    *,
    ctx: ToolContext,
    meta_client,
    resumo_memoria: str,
    memoria_negocio: dict,
    historico: list[dict],
    mensagem_atual: str,
    nivel_tecnico: str,
    anthropic_api_key: str,
    anthropic_workspace_id: str,
) -> dict:
    """One turn of the agent loop: builds context, routes to Haiku/Sonnet,
    runs the tool-use loop until Claude returns a final text answer."""
    model = MODEL_SONNET if classify_intent(mensagem_atual) == "estrategia" else MODEL_HAIKU

    headers = {}
    if anthropic_workspace_id:
        headers["anthropic-workspace-id"] = anthropic_workspace_id
    client = anthropic.AsyncAnthropic(api_key=anthropic_api_key, default_headers=headers)

    context_note = (
        f"Nível técnico: {nivel_tecnico}. Resumo da conversa: {resumo_memoria or 'nenhum ainda'}. "
        f"Memória de negócio: {memoria_negocio or 'nenhuma ainda'}."
    )
    messages = [
        {"role": "user", "content": context_note},
        *historico,
        {"role": "user", "content": mensagem_atual},
    ]

    total_input = 0
    total_output = 0

    for _ in range(5):  # hard cap on tool-use round-trips per turn
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens

        if response.stop_reason != "tool_use":
            text = next((b.text for b in response.content if getattr(b, "type", "") == "text"), "")
            return {
                "resposta": text,
                "tokens_input": total_input,
                "tokens_output": total_output,
                "modelo_usado": model,
            }

        tool_block = next(b for b in response.content if getattr(b, "type", "") == "tool_use")
        try:
            tool_result = await dispatch_tool(tool_block.name, tool_block.input, ctx, meta_client)
            tool_content = str(tool_result)
        except Exception as exc:
            logger.warning("Tool %s failed: %s", tool_block.name, exc)
            tool_content = f"Erro: {exc}"

        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": tool_content}],
            }
        )

    return {
        "resposta": "Deixa eu processar isso com mais calma, já te chamo.",
        "tokens_input": total_input,
        "tokens_output": total_output,
        "modelo_usado": model,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/unit/test_agent_llm.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/llm.py campaign_optimizer/gestor-ads/backend/tests/unit/test_agent_llm.py
git commit -m "feat(gestor-ads): agent LLM loop — model routing, tool use, prompt caching"
```

---

## Task 12: Webhook router + agent FastAPI app

**Files:**
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/router.py`
- Create: `campaign_optimizer/gestor-ads/backend/app/agent/main.py`
- Test: `campaign_optimizer/gestor-ads/backend/tests/integration/test_agent_router.py`

**Interfaces:**
- Consumes: `TelegramAdapter`, `EvolutionAdapter` (Tasks 4–5), `get_or_create_conversation`/`record_message`/`update_memory` (Task 7), `run_agent_turn` (Task 11), `transcribe_audio` (Task 6), `build_meta_client`/`get_supabase` (existing `app/dependencies.py`).
- Produces: `POST /agent/telegram/webhook`, `POST /agent/evolution/webhook` — both return `{"ok": true}` immediately and process via `BackgroundTasks`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_agent_router.py
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.agent.main import app


def test_telegram_webhook_acks_immediately():
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        client = TestClient(app)
        payload = {"message": {"chat": {"id": 555}, "text": "oi"}}
        response = client.post("/agent/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_evolution_webhook_acks_immediately():
    with patch("app.agent.router.process_incoming_message", new=AsyncMock()):
        client = TestClient(app)
        payload = {"data": {"key": {"remoteJid": "5585999@s.whatsapp.net"}, "message": {"conversation": "oi"}}}
        response = client.post("/agent/evolution/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/integration/test_agent_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agent.router'`.

- [ ] **Step 3: Write `router.py`**

```python
# app/agent/router.py
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from supabase import Client

from app.agent.channels.base import IncomingMessage
from app.agent.channels.evolution import EvolutionAdapter
from app.agent.channels.telegram import TelegramAdapter
from app.agent.conversation import get_or_create_conversation, record_message, update_memory
from app.agent.llm import run_agent_turn
from app.agent.tools import ToolContext
from app.agent.transcription import transcribe_audio
from app.config import Settings, get_settings
from app.dependencies import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


def _adapter_for(channel: str, settings: Settings):
    if channel == "telegram":
        return TelegramAdapter(bot_token=settings.telegram_bot_token)
    return EvolutionAdapter(
        base_url=settings.evolution_base_url,
        api_key=settings.evolution_api_key,
        instance=settings.evolution_instance,
    )


async def process_incoming_message(msg: IncomingMessage, settings: Settings, supabase: Client) -> None:
    """Runs off the request/response cycle — this is what BackgroundTasks calls."""
    adapter = _adapter_for(msg.channel, settings)
    conv = await get_or_create_conversation(supabase, msg.channel, msg.channel_user_id)

    texto = msg.text or ""
    if msg.audio_bytes:
        try:
            texto = await transcribe_audio(msg.audio_bytes, settings.openai_api_key)
        except Exception:
            await adapter.send_text(msg.channel_user_id, "Não consegui entender o áudio, pode repetir em texto?")
            return

    if not conv.get("owner_id"):
        from app.auth.meta_oauth import generate_oauth_url

        url = generate_oauth_url(user_id="", conversation_id=conv["id"])
        await adapter.send_text(
            msg.channel_user_id,
            f"Oi! Pra começar, conecte sua conta Meta clicando aqui: {url}",
        )
        return

    await record_message(supabase, conv["id"], "user", texto)

    profile = (
        supabase.table("profiles").select("nivel_tecnico").eq("id", conv["owner_id"]).execute().data
    )
    nivel_tecnico = profile[0]["nivel_tecnico"] if profile else "avancado"

    ctx = ToolContext(
        supabase=supabase,
        settings=settings,
        user_id=conv["owner_id"],
        conversation_id=conv["id"],
        ad_account_id=conv.get("ad_account_id"),
    )

    meta_client = None
    if conv.get("ad_account_id"):
        from app.dependencies import build_meta_client
        from app.auth.models import User

        acc = supabase.table("ad_accounts").select("external_id").eq("id", conv["ad_account_id"]).single().execute().data
        meta_client = await build_meta_client(acc["external_id"], User(id=conv["owner_id"], email=""), supabase, settings)

    result = await run_agent_turn(
        ctx=ctx,
        meta_client=meta_client,
        resumo_memoria=conv.get("resumo_memoria", ""),
        memoria_negocio=conv.get("memoria_negocio", {}),
        historico=[],
        mensagem_atual=texto,
        nivel_tecnico=nivel_tecnico,
        anthropic_api_key=settings.anthropic_api_key,
        anthropic_workspace_id=settings.anthropic_workspace_id,
    )

    await record_message(
        supabase, conv["id"], "assistant", result["resposta"],
        modelo_usado=result["modelo_usado"], tokens_input=result["tokens_input"], tokens_output=result["tokens_output"],
    )
    await adapter.send_text(msg.channel_user_id, result["resposta"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    supabase: Client = Depends(get_supabase),
):
    adapter = TelegramAdapter(bot_token=settings.telegram_bot_token)
    msg = await adapter.receive_webhook(payload)
    background_tasks.add_task(process_incoming_message, msg, settings, supabase)
    return {"ok": True}


@router.post("/evolution/webhook")
async def evolution_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    supabase: Client = Depends(get_supabase),
):
    adapter = EvolutionAdapter(
        base_url=settings.evolution_base_url, api_key=settings.evolution_api_key, instance=settings.evolution_instance
    )
    msg = await adapter.receive_webhook(payload)
    background_tasks.add_task(process_incoming_message, msg, settings, supabase)
    return {"ok": True}
```

- [ ] **Step 4: Write `main.py`**

```python
# app/agent/main.py
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.agent.router import router as agent_router
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="Gestor Ads — Agente Conversacional", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(agent_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest tests/integration/test_agent_router.py -v`
Expected: PASS (2 tests). Note: `TestClient` calls run `BackgroundTasks` synchronously before
returning the response in this FastAPI version, but since `process_incoming_message` is
patched out in both tests, this doesn't affect the ack-only assertion being tested.

- [ ] **Step 6: Run the full test suite**

Run: `cd campaign_optimizer/gestor-ads/backend && uv run pytest -v`
Expected: PASS — every test file created/modified in Tasks 1–12, plus all pre-existing tests
unaffected.

- [ ] **Step 7: Commit**

```bash
git add campaign_optimizer/gestor-ads/backend/app/agent/router.py campaign_optimizer/gestor-ads/backend/app/agent/main.py campaign_optimizer/gestor-ads/backend/tests/integration/test_agent_router.py
git commit -m "feat(gestor-ads): agent webhook router + FastAPI app (Telegram + Evolution)"
```

---

## Task 13: Docker — new `creative_ads_agent` service

**Files:**
- Modify (on the VPS, not in this git repo — see `vps-acesso` memory: there is no
  `docker-compose.yml` tracked in git, it lives only at `/opt/creative-ads/saas/docker-compose.yml`):
  add a new service block, reusing the **same image** already built for
  `creative_ads_backend` (same `Dockerfile`, same `app/` — the agent module is just another
  entrypoint in the same package, per this plan's Architecture section).

**Interfaces:**
- Consumes: the existing `Dockerfile` in `campaign_optimizer/gestor-ads/backend/` (no changes needed — it already `COPY`s the whole `app/` directory, which now includes `app/agent/`).
- Produces: a running `creative_ads_agent` container reachable by Telegram's webhook URL and by the `evolution-go` container on the same VPS network.

- [ ] **Step 1: Confirm no Dockerfile change is needed**

Run: `cd campaign_optimizer/gestor-ads/backend && docker build -t gestor-ads-test .` (local
verification only — this doesn't touch the VPS). Expected: builds successfully; `app/agent/`
is included because the Dockerfile already does `COPY app/ app/` (no per-module COPY lines to
update).

- [ ] **Step 2: Document the new compose service block**

Add this to `/opt/creative-ads/saas/docker-compose.yml` on the VPS (same file that already
has `creative_ads_backend`/`creative_ads_frontend`), following the exact deploy process in
the `vps-acesso` memory (tar the backend dir including `app/agent/`, scp, extract, rebuild):

```yaml
  creative_ads_agent:
    build:
      context: ./backend
    container_name: creative_ads_agent
    command: ["uv", "run", "uvicorn", "app.agent.main:app", "--host", "0.0.0.0", "--port", "8001"]
    env_file:
      - .env.production
    restart: unless-stopped
    networks:
      - default
```

Notes for whoever applies this on the VPS:
- No new `EXPOSE` needed in the Dockerfile — the port is passed via `command`, same image.
- Traefik routing for `POST /agent/telegram/webhook` and `POST /agent/evolution/webhook` needs
  a new router rule (e.g. `Host(agent.creativeagenciamkt.com.br)` or a `PathPrefix(/agent)` on
  the existing host, matching whichever pattern is simpler given the current Traefik labels
  already in use for `creative_ads_backend`).
- The `evolution-go` container already running on this VPS (per `vps-acesso` memory) must be
  configured to POST its webhook to this new service's `/agent/evolution/webhook` endpoint —
  this is an Evolution API instance-level setting, not a compose change.
- Set `TELEGRAM_BOT_TOKEN`, `EVOLUTION_BASE_URL` (likely `http://evolution-go:8080` if on the
  same Docker network), `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `OPENAI_API_KEY` in
  `.env.production` before starting this service (Task 2's new `Settings` fields).

- [ ] **Step 3: No commit for this task**

This task only touches the VPS-only compose file (not tracked in git, per the `vps-acesso`
memory) — nothing to commit in this repository. The next actual deploy of the backend image
naturally picks up `app/agent/` since it's already inside the existing `COPY app/ app/` line.

---

## Self-Review Notes

**Spec coverage:** §1 scope (Telegram+Evolution, onboarding, campaign creation, radius
targeting, on-demand reports, audio, cost routing) → Tasks 3–13. §2 architecture (shared
core, separate container) → Task 13 + Architecture section. §3 data model → Task 1. §4 agent
loop → Tasks 9–11. §5 onboarding → Task 8. §6 cost → Task 11 (routing + caching). §7 errors →
handled inline in Task 12's `process_incoming_message` (audio failure) and Task 10's
`criar_campanha` (draft validation); Evolution session-down alerting and LLM timeout retry are
**not** implemented as separate code in this plan — flagging this gap: those two error paths
from spec §7 ("sessão do Evolution cair → alerta admin", "timeout do LLM → reprocessa em
background") need operational monitoring (e.g. a simple health check hitting Evolution's
status endpoint) that doesn't fit cleanly into a single task here. Recommend a short follow-up
task once the agent is running and real failure modes are observed, rather than guessing at
alerting thresholds now (YAGNI — spec §9 already defers proactive alerting to Fase 3b, and
these two error paths are the same category of work). §8 security → reused as-is from Fase 1,
no new task needed. §9 out-of-scope → correctly excluded from every task above.

**Placeholder scan:** no TBD/TODO; every step has real code.

**Type consistency:** `ToolContext` fields match across Tasks 9, 10, 11 (`supabase`,
`settings`, `user_id`, `conversation_id`, `ad_account_id`). `IncomingMessage` fields match
across Tasks 3–5 and 12. `run_agent_turn`'s return shape (`resposta`/`tokens_input`/
`tokens_output`/`modelo_usado`) matches what Task 12's `process_incoming_message` consumes.
