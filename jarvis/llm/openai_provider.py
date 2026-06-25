"""OpenAI (and OpenAI-compatible) chat provider.

The ``openai`` SDK is imported lazily so the app runs without it installed.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import LLMMessage, LLMProvider, LLMResponse, ToolCall


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        super().__init__(model=model)
        self._client = None

    def default_model(self) -> str:
        return "gpt-4o-mini"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        from openai import OpenAI  # lazy import

        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
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
                text="The 'openai' package is not installed. Run: pip install openai",
                error="missing_dependency",
            )
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(text=f"OpenAI client error: {exc}", error=str(exc))

        payload_messages = [_to_openai_message(m) for m in messages]
        request: dict[str, Any] = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        try:
            completion = client.chat.completions.create(**request)
        except Exception as exc:  # noqa: BLE001 - surface as graceful error
            return LLMResponse(text=f"OpenAI request failed: {exc}", error=str(exc))

        choice = completion.choices[0].message
        tool_calls: list[ToolCall] = []
        for tc in getattr(choice, "tool_calls", None) or []:
            import json

            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return LLMResponse(
            text=choice.content or "",
            tool_calls=tool_calls,
            raw=completion,
        )


def _to_openai_message(m: LLMMessage) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": m.role, "content": m.content}
    if m.role == "tool" and m.tool_call_id:
        msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
    return msg
