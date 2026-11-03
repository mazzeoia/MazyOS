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
        # WhatsApp sends extendedTextMessage for replies, quotes and links.
        text = message.get("conversation") or message.get("extendedTextMessage", {}).get("text")

        location = None
        loc = message.get("locationMessage")
        if loc:
            location = (loc["degreesLatitude"], loc["degreesLongitude"])

        audio_msg = message.get("audioMessage")
        audio_ref = audio_msg.get("url", "") if audio_msg else None

        return IncomingMessage(
            channel="evolution",
            channel_user_id=phone,
            raw=payload,
            text=text,
            audio_ref=audio_ref,
            location=location,
        )

    async def download_media(self, file_ref: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base_url}/chat/getBase64FromMediaMessage/{self._instance}",
                headers={"apikey": self._api_key},
                json={"message": {"url": file_ref}},
            )
            b64 = resp.json().get("base64", "")
            return base64.b64decode(b64) if b64 else b""
