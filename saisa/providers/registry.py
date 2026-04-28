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
from .base import LLMProvider


def get_provider(name: str | None = None) -> LLMProvider:
    """Return a ready-to-use provider instance."""
    provider_name = (name or PROVIDER).strip().lower()

    if provider_name == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)

    if provider_name == "groq":
        from .groq_provider import GroqProvider

        return GroqProvider(api_key=GROQ_API_KEY, model=GROQ_MODEL)

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

    if provider_name in ("anthropic", "claude"):
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=ANTHROPIC_API_KEY, model=ANTHROPIC_MODEL)

    raise ValueError(
        f"Unknown provider '{provider_name}'. "
        "Supported: ollama, groq, openai, anthropic"
    )
