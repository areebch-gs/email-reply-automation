import os
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


def get_provider():
    """
    Return the configured LLM provider.

    Set LLM_PROVIDER in .env to switch:
        LLM_PROVIDER=openai    → GPT-4o-mini  (default)
        LLM_PROVIDER=claude    → Claude 3.5 Haiku

    Override the model with LLM_MODEL:
        LLM_MODEL=gpt-4o
        LLM_MODEL=claude-opus-4-5
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    if provider == "claude":
        model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
        return AnthropicProvider(model=model)

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    return OpenAIProvider(model=model)
