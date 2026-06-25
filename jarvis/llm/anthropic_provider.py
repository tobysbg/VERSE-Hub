"""Anthropic (Claude) chat provider.

The ``anthropic`` SDK is imported lazily so the app runs without it installed.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "") -> None:
        self.api_key = api_key
        super().__init__(model=model)
        self._client = None

    def default_model(self) -> str:
        return "claude-3-5-sonnet-latest"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        from anthropic import Anthropic  # lazy import

        self._client = Anthropic(api_key=self.api_key)
        return self._client

    def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if not self.is_configured():
            return self._not_configured_response()
        try:
            client = self._get_client()
        except ImportError:
            return LLMResponse(
                text="The 'anthropic' package is not installed. Run: pip install anthropic",
                error="missing_dependency",
            )
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(text=f"Anthropic client error: {exc}", error=str(exc))

        system_prompt, conv = _split_system(messages)
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": temperature,
            "messages": conv,
        }
        if system_prompt:
            request["system"] = system_prompt
        if tools:
            request["tools"] = [_to_anthropic_tool(t) for t in tools]

        try:
            message = client.messages.create(**request)
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(text=f"Anthropic request failed: {exc}", error=str(exc))

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in message.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
            elif getattr(block, "type", None) == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=dict(block.input or {}))
                )

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            raw=message,
        )


def _split_system(messages: list[LLMMessage]) -> tuple[str, list[dict[str, Any]]]:
    system_parts: list[str] = []
    conv: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "system":
            system_parts.append(m.content)
        elif m.role == "tool":
            # Represent tool results as a user message block.
            conv.append({"role": "user", "content": f"[tool result] {m.content}"})
        elif m.role == "assistant" and m.tool_calls and not m.content:
            # A pure tool-call turn has no text; Anthropic rejects empty content,
            # so describe the requested calls instead.
            names = ", ".join(tc.name for tc in m.tool_calls)
            conv.append({"role": "assistant", "content": f"(requesting tools: {names})"})
        else:
            conv.append({"role": m.role, "content": m.content})
    return "\n\n".join(system_parts), conv


def _to_anthropic_tool(openai_tool: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI-style tool schema to Anthropic's format."""
    fn = openai_tool.get("function", openai_tool)
    return {
        "name": fn.get("name", ""),
        "description": fn.get("description", ""),
        "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
    }
