import httpx

from ..config import get_settings
from .errors import ProviderError, from_openai, network


async def transcribe(audio: bytes, filename: str, content_type: str, language: str) -> str:
    s = get_settings()
    if s.stt_provider != "openai":
        raise ProviderError(400, "stt_not_server_side", "Server STT is off. The browser's own speech recognition is used instead.")
    if not s.openai_api_key:
        raise ProviderError(503, "missing_api_key", "OPENAI_API_KEY is not set in .env.")
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {s.openai_api_key}"},
                data={"model": s.openai_stt_model, "language": language},
                files={"file": (filename, audio, content_type)},
            )
    except httpx.HTTPError:
        raise network()
    if r.status_code != 200:
        raise from_openai(r.status_code)
    return (r.json().get("text") or "").strip()
