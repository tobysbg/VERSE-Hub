"""Factory that builds the configured LLM provider from Settings."""
from __future__ import annotations

from ..app.settings import Settings
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider


def get_provider(settings: Settings) -> LLMProvider:
    """Return an LLMProvider instance for the currently selected provider."""
    provider = (settings.llm_provider or "openai").lower()
    model = settings.llm_model

    if provider == "anthropic":
        return AnthropicProvider(api_key=settings.anthropic_api_key, model=model)
    if provider == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url, model=model)
    # Default to OpenAI / OpenAI-compatible.
    return OpenAIProvider(api_key=settings.openai_api_key, model=model)
