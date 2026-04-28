"""Provider tiers — free (Ollama local) + cloud API tiers.

SAISA works 100% free with Ollama (local models).
Adding API keys unlocks more powerful cloud models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class ProviderTier:
    name: str
    provider: str
    cost: str
    speed: str
    quality: str
    requires_key: bool
    models: list[str]
    description: str


TIERS: list[ProviderTier] = [
    ProviderTier(
        name="Free (Local)",
        provider="ollama",
        cost="Free forever",
        speed="Depends on hardware",
        quality="Good (7B-70B models)",
        requires_key=False,
        models=["llama3.2", "codellama", "deepseek-coder-v2", "qwen2.5-coder", "mistral"],
        description="100% local, 100% private. No internet needed. Run any open-source model.",
    ),
    ProviderTier(
        name="Turbo (Groq)",
        provider="groq",
        cost="Free tier available / Pay as you go",
        speed="Ultra-fast (~500 tok/s)",
        quality="Excellent (70B models)",
        requires_key=True,
        models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        description="Blazing fast cloud inference. Free tier with rate limits.",
    ),
    ProviderTier(
        name="Premium (OpenAI)",
        provider="openai",
        cost="Pay per token",
        speed="Fast",
        quality="Top tier (GPT-4o)",
        requires_key=True,
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        description="OpenAI's most capable models. Best for complex reasoning.",
    ),
    ProviderTier(
        name="Elite (Anthropic)",
        provider="anthropic",
        cost="Pay per token",
        speed="Fast",
        quality="Top tier (Claude)",
        requires_key=True,
        models=["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
        description="Anthropic Claude. Excellent for coding and long context.",
    ),
]


def get_tier(provider: str) -> ProviderTier | None:
    """Get tier info for a provider."""
    for tier in TIERS:
        if tier.provider == provider:
            return tier
    return None


def list_tiers() -> str:
    """List all available tiers as formatted text."""
    lines: list[str] = []
    for tier in TIERS:
        key_status = "API key required" if tier.requires_key else "No key needed"
        lines.append(f"\n{'=' * 50}")
        lines.append(f"  {tier.name}")
        lines.append(f"  Provider: {tier.provider}")
        lines.append(f"  Cost: {tier.cost}")
        lines.append(f"  Speed: {tier.speed}")
        lines.append(f"  Quality: {tier.quality}")
        lines.append(f"  Auth: {key_status}")
        lines.append(f"  Models: {', '.join(tier.models)}")
        lines.append(f"  {tier.description}")
    return "\n".join(lines)


def list_tiers_json() -> str:
    """List tiers as JSON."""
    return json.dumps(
        [
            {
                "name": t.name,
                "provider": t.provider,
                "cost": t.cost,
                "speed": t.speed,
                "quality": t.quality,
                "requires_key": t.requires_key,
                "models": t.models,
                "description": t.description,
            }
            for t in TIERS
        ],
        indent=2,
    )


def recommend_tier(
    budget: str = "free",
    priority: str = "balanced",
) -> ProviderTier:
    """Recommend a tier based on budget and priority.

    budget: "free", "low", "unlimited"
    priority: "speed", "quality", "balanced", "privacy"
    """
    if budget == "free" or priority == "privacy":
        return TIERS[0]  # Ollama
    if priority == "speed":
        return TIERS[1]  # Groq
    if priority == "quality":
        return TIERS[3]  # Anthropic
    if budget == "low":
        return TIERS[1]  # Groq (free tier)
    return TIERS[2]  # OpenAI (balanced)
