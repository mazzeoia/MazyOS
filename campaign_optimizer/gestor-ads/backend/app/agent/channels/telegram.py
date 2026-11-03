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

        return IncomingMessage(
            channel="telegram",
            channel_user_id=chat_id,
            raw=payload,
            text=message.get("text"),
            audio_ref=audio_file_id,
            location=location,
        )

    async def download_media(self, file_ref: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.BASE}/bot{self._token}/getFile", params={"file_id": file_ref})
            file_path = resp.json()["result"]["file_path"]
            file_resp = await client.get(f"{self.BASE}/file/bot{self._token}/{file_path}")
            return file_resp.content
