"""Audio transcription via OpenAI Whisper REST API."""
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
