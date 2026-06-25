"""LLM provider abstraction.

Every provider implements the same small interface so the agent loop is fully
decoupled from any single vendor. Providers must NEVER raise on construction
when keys are missing - they report ``is_configured() == False`` and return a
friendly message from ``chat`` instead.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMMessage:
    """A provider-neutral chat message."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    # Optional structured tool-call payloads (provider-specific shape kept opaque).
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class ToolCall:
    """A request from the model to invoke a named tool with JSON arguments."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """The result of a single chat completion."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class LLMProvider(abc.ABC):
    """Abstract base for all chat providers."""

    name: str = "base"

    def __init__(self, model: str = "") -> None:
        self.model = model or self.default_model()

    @abc.abstractmethod
    def default_model(self) -> str:
        ...

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider can actually make a request."""

    @abc.abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Run a single completion. Must not raise; return an error response."""

    # Shared helper so every provider gives the same graceful message.
    def _not_configured_response(self) -> LLMResponse:
        return LLMResponse(
            text=(
                f"The '{self.name}' provider is not configured. Open Settings and "
                f"add an API key (or choose a different provider) to enable chat."
            ),
            error="not_configured",
        )
