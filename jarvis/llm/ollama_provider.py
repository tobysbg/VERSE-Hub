"""Ollama local-model chat provider (talks to a local Ollama server over HTTP).

Uses ``httpx`` (a core dependency). No API key required; "configured" simply
means a base URL is set. Network reachability is checked lazily at call time so
construction never blocks or raises.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import LLMMessage, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "") -> None:
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        super().__init__(model=model)

    def default_model(self) -> str:
        return "llama3.1"

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def chat(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if not self.is_configured():
            return self._not_configured_response()
        try:
            import httpx
        except ImportError:
            return LLMResponse(
                text="The 'httpx' package is not installed. Run: pip install httpx",
                error="missing_dependency",
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": _norm_role(m.role), "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(
                text=(
                    f"Could not reach Ollama at {self.base_url}. Is it running? "
                    f"(error: {exc})"
                ),
                error=str(exc),
            )

        message = data.get("message", {}) or {}
        return LLMResponse(text=message.get("content", "") or "", raw=data)


def _norm_role(role: str) -> str:
    # Ollama understands system/user/assistant; map tool -> user.
    return role if role in {"system", "user", "assistant"} else "user"
