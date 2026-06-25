"""OpenAI (and OpenAI-compatible) chat provider.

The ``openai`` SDK is imported lazily so the app runs without it installed.
"""
from __future__ import annotations

import json
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

        payload_messages = to_openai_messages(messages)
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


def sanitize_tool_messages(messages: list[LLMMessage]) -> list[LLMMessage]:
    """Drop orphan ``tool`` messages to satisfy the Chat Completions API.

    A ``role="tool"`` message is only valid when it *immediately* follows an
    assistant message whose ``tool_calls`` include a matching ``tool_call_id``.
    Any tool message that does not satisfy this (e.g. left over in memory from an
    earlier buggy turn, or with a mismatched id) is removed. The relative order
    of all surviving messages is preserved.
    """
    cleaned: list[LLMMessage] = []
    # ids of tool_calls announced by the most recent assistant message that have
    # not yet been answered. Reset by any non-tool message.
    pending_ids: set[str] = set()

    for msg in messages:
        if msg.role == "tool":
            if msg.tool_call_id and msg.tool_call_id in pending_ids:
                cleaned.append(msg)
                pending_ids.discard(msg.tool_call_id)
            # else: orphan / mismatched -> drop it.
            continue

        cleaned.append(msg)
        if msg.role == "assistant" and msg.tool_calls:
            pending_ids = {tc.id for tc in msg.tool_calls}
        else:
            pending_ids = set()

    return cleaned


def _to_openai_message(m: LLMMessage) -> dict[str, Any]:
    if m.role == "assistant" and m.tool_calls:
        return {
            "role": "assistant",
            # Content may be empty on a pure tool-call turn; OpenAI accepts None.
            "content": m.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments or {}),
                    },
                }
                for tc in m.tool_calls
            ],
        }
    if m.role == "tool":
        msg: dict[str, Any] = {"role": "tool", "content": m.content}
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        return msg
    return {"role": m.role, "content": m.content}


def to_openai_messages(messages: list[LLMMessage]) -> list[dict[str, Any]]:
    """Sanitize, then serialize messages into the OpenAI Chat Completions shape."""
    return [_to_openai_message(m) for m in sanitize_tool_messages(messages)]
