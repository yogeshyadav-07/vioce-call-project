class ProviderError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def from_openai(status: int) -> ProviderError:
    if status == 401:
        return ProviderError(502, "bad_api_key", "OpenAI rejected the API key. Check OPENAI_API_KEY in .env.")
    if status == 429:
        return ProviderError(502, "quota", "OpenAI quota or rate limit reached. Check billing/usage.")
    return ProviderError(502, "provider_failed", f"OpenAI request failed (HTTP {status}).")


def network() -> ProviderError:
    return ProviderError(502, "network", "Could not reach the AI provider (network error or timeout).")
