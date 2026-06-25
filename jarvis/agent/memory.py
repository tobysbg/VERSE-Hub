"""Short-term conversation memory for the agent.

Keeps a bounded list of provider-neutral messages used to seed each LLM request.
Only durable conversation turns live here - user messages and final
natural-language assistant answers. The intermediate assistant-tool_call and
tool-result messages are kept in a per-request working transcript inside the
agent loop and are deliberately NOT stored here, so the long-term history can
never contain an orphan ``role="tool"`` message.
"""
from __future__ import annotations

from ..llm.base import LLMMessage


class ConversationMemory:
    def __init__(self, system_prompt: str = "", max_messages: int = 40) -> None:
        self.system_prompt = system_prompt
        self.max_messages = max_messages
        self._messages: list[LLMMessage] = []

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def add_user(self, content: str) -> None:
        self._add(LLMMessage(role="user", content=content))

    def add_assistant(self, content: str) -> None:
        self._add(LLMMessage(role="assistant", content=content))

    def _add(self, message: LLMMessage) -> None:
        self._messages.append(message)
        # Trim oldest non-system messages beyond the window.
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

    def build(self) -> list[LLMMessage]:
        prefix = [LLMMessage(role="system", content=self.system_prompt)] if self.system_prompt else []
        return prefix + list(self._messages)

    def clear(self) -> None:
        self._messages.clear()
