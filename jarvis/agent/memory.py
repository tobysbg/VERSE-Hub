"""Short-term conversation memory for the agent.

Keeps a bounded list of provider-neutral messages used to build each LLM
request. Long-term history lives in SQLite (see storage.database); this is the
working window passed to the model.
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

    def add_tool_result(self, content: str, name: str = "", tool_call_id: str = "") -> None:
        self._add(LLMMessage(role="tool", content=content, name=name, tool_call_id=tool_call_id))

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
