import pytest
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
