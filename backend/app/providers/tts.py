from ..config import get_settings
from .errors import ProviderError, from_openai
from .http import post


async def synthesize(text: str) -> bytes:
    s = get_settings()
    if s.tts_provider != "openai":
        raise ProviderError(400, "tts_not_server_side", "Server TTS is off. The browser's speech synthesis is used instead.")
    if not s.openai_api_key:
        raise ProviderError(503, "missing_api_key", "OPENAI_API_KEY is not set in .env.")
    r = await post("https://api.openai.com/v1/audio/speech", timeout=40, headers={"Authorization": f"Bearer {s.openai_api_key}"},
                   json={"model": s.openai_tts_model, "voice": s.openai_tts_voice, "input": text, "response_format": "mp3"})
    if r.status_code != 200:
        raise from_openai(r.status_code)
    return r.content
