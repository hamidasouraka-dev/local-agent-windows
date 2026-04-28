"""Provider registry — instantiate by name."""

from __future__ import annotations

from ..config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    PROVIDER,
)
from ..errors import (
    APIKeyMissingError,
    InvalidProviderError,
    ProviderConnectionError,
)
from .base import LLMProvider

SUPPORTED_PROVIDERS = ("ollama", "groq", "openai", "anthropic", "claude")


def get_provider(name: str | None = None) -> LLMProvider:
    """Return a ready-to-use provider instance.

    Raises:
        InvalidProviderError: Unknown provider name.
        APIKeyMissingError: Cloud provider without API key.
        ProviderConnectionError: Cannot reach the provider.
    """
    provider_name = (name or PROVIDER).strip().lower()

    if provider_name == "ollama":
        from .ollama import OllamaProvider

        try:
            return OllamaProvider(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
        except ConnectionError as e:
            raise ProviderConnectionError("ollama", OLLAMA_BASE_URL, e) from e

    if provider_name == "groq":
        if not GROQ_API_KEY:
            raise APIKeyMissingError("groq")
        from .groq_provider import GroqProvider

        return GroqProvider(api_key=GROQ_API_KEY, model=GROQ_MODEL)

    if provider_name == "openai":
        if not OPENAI_API_KEY:
            raise APIKeyMissingError("openai")
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

    if provider_name in ("anthropic", "claude"):
        if not ANTHROPIC_API_KEY:
            raise APIKeyMissingError("anthropic")
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL)

    raise InvalidProviderError(provider_name)
