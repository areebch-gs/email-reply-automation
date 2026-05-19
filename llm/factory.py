import os
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


def get_provider(provider: str | None = None, model: str | None = None):
    """
    Return the configured LLM provider.

    Args override .env values when supplied:
        provider — "openai" or "claude"
        model    — any valid model ID for the chosen provider

    Falls back to LLM_PROVIDER / LLM_MODEL env vars, then hardcoded defaults.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower().strip()

    if provider == "claude":
        model = model or os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        return AnthropicProvider(model=model)

    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    return OpenAIProvider(model=model)
