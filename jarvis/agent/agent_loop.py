"""The tool-using agent loop.

Flow per user request:
    classify intent -> log -> ask the LLM (with tool schemas) ->
    for each requested tool call:
        validate args -> safety.evaluate ->
            BLOCK   : record refusal, feed back to model
            CONFIRM : ask the user via the confirm callback
            ALLOW   : run it
        observe the result and feed it back to the model
    repeat until the model stops requesting tools (or a limit is hit) ->
    return the final assistant message.

The loop is framework-agnostic: it talks to the UI through a small set of
callbacks and checks a ``threading.Event`` stop flag between every step, so the
HUD's Stop button cancels promptly. This makes it directly unit-testable with a
fake LLM provider and fake callbacks.
"""
from __future__ import annotations

import enum
import threading
from dataclasses import dataclass
from typing import Callable, Optional

from ..llm.base import LLMProvider, ToolCall
from ..storage.database import Database
from ..storage.models import (
    ActionLogEntry,
    AgentMode,
    AgentStatus,
    MessageRole,
    RiskLevel,
)
from ..tools.base_tool import BaseTool, ToolResult
from ..tools.registry import ToolRegistry
from .memory import ConversationMemory
from .planner import classify_intent
from .prompts import build_system_prompt
from .safety import SafetyDecision, SafetyManager

MAX_TOOL_ITERATIONS = 8


class ConfirmDecision(str, enum.Enum):
    ALLOW_ONCE = "allow_once"
    ALWAYS = "always"
    DENY = "deny"


@dataclass
class ConfirmRequest:
    """Passed to the confirm callback so the UI can render the dialog."""

    tool_name: str
    preview: str
    why: str
    risk: RiskLevel
    allow_once_only: bool


# Callback signatures (all optional; default to no-ops).
StatusCb = Callable[[AgentStatus], None]
TimelineCb = Callable[[str], None]
MessageCb = Callable[[str], None]
ConfirmCb = Callable[[ConfirmRequest], ConfirmDecision]


def _noop(*_a, **_k) -> None:
    return None


def _auto_deny(_req: ConfirmRequest) -> ConfirmDecision:
    return ConfirmDecision.DENY


@dataclass
class AgentCallbacks:
    on_status: StatusCb = _noop
    on_timeline: TimelineCb = _noop
    on_assistant_message: MessageCb = _noop
    confirm: ConfirmCb = _auto_deny


class AgentLoop:
    def __init__(
        self,
        provider: LLMProvider,
        registry: ToolRegistry,
        safety: SafetyManager,
        memory: ConversationMemory,
        db: Database,
        session_id: int,
        callbacks: Optional[AgentCallbacks] = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.safety = safety
        self.memory = memory
        self.db = db
        self.session_id = session_id
        self.cb = callbacks or AgentCallbacks()
        self._stop = threading.Event()

    # -- control -------------------------------------------------------------
    def request_stop(self) -> None:
        self._stop.set()

    def reset_stop(self) -> None:
        self._stop.clear()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    # -- main entrypoint -----------------------------------------------------
    def handle(self, user_text: str) -> str:
        """Process one user request and return the final assistant reply."""
        self.reset_stop()
        settings = self.safety.settings
        self.memory.set_system_prompt(build_system_prompt(settings))

        intent = classify_intent(user_text)
        self.db.add_message(self.session_id, MessageRole.USER, user_text)
        self.memory.add_user(user_text)
        self.cb.on_timeline(f"Received request (intent: {intent.value}).")

        if not self.provider.is_configured():
            msg = self.provider.chat(self.memory.build()).text
            self._finish_assistant(msg)
            return msg

        # Which tools are exposed depends on enabled capabilities and mode.
        tools = self._exposed_tools(settings.agent_mode)
        schemas = self.registry.schemas(tools) if tools else None

        for _ in range(MAX_TOOL_ITERATIONS):
            if self.stopped:
                return self._stop_message()

            self.cb.on_status(AgentStatus.THINKING)
            response = self.provider.chat(self.memory.build(), tools=schemas)

            if not response.ok and not response.text:
                self.cb.on_status(AgentStatus.ERROR)
                err = f"LLM error: {response.error}"
                self._finish_assistant(err)
                return err

            # No tool calls -> this is the final answer.
            if not response.tool_calls:
                self._finish_assistant(response.text)
                return response.text

            # Record any interim assistant text.
            if response.text:
                self.memory.add_assistant(response.text)

            for call in response.tool_calls:
                if self.stopped:
                    return self._stop_message()
                self._run_tool_call(call, user_text, intent.value)

        # Safety net if the model keeps looping.
        final = "I've reached the tool-call limit for this request. Stopping here."
        self._finish_assistant(final)
        return final

    # -- per tool-call -------------------------------------------------------
    def _run_tool_call(self, call: ToolCall, user_text: str, plan: str) -> None:
        tool = self.registry.get(call.name)
        if tool is None:
            self._feed_tool_result(call, ToolResult.fail(f"Unknown tool: {call.name}"))
            return

        args, err = tool.safe_validate(call.arguments)
        if err or args is None:
            self._feed_tool_result(call, ToolResult.fail(err or "invalid arguments"))
            return

        preview = tool.preview(args)
        result = self.safety.evaluate(tool, args)
        self.cb.on_timeline(f"{tool.name}: {preview} [risk: {result.risk.value}]")

        if result.decision == SafetyDecision.BLOCK:
            self.cb.on_status(AgentStatus.ERROR)
            self._log(user_text, plan, tool, preview, result.risk, "blocked",
                      ToolResult.fail(result.block_message))
            self._feed_tool_result(call, ToolResult.fail(result.block_message))
            return

        if result.decision == SafetyDecision.CONFIRM:
            self.cb.on_status(AgentStatus.NEEDS_CONFIRMATION)
            decision = self.cb.confirm(
                ConfirmRequest(
                    tool_name=tool.name,
                    preview=tool.preview(args),
                    why="; ".join(result.reasons),
                    risk=result.risk,
                    allow_once_only=result.allow_once_only,
                )
            )
            if decision == ConfirmDecision.DENY:
                self._log(user_text, plan, tool, preview, result.risk, "denied",
                          ToolResult.fail("User denied."))
                self._feed_tool_result(call, ToolResult.fail("The user denied this action."))
                return
            if decision == ConfirmDecision.ALWAYS and not result.allow_once_only:
                self.safety.grant_session(tool.name)
            confirmation = decision.value
        else:
            confirmation = "not required"

        # Execute.
        self.cb.on_status(AgentStatus.ACTING)
        try:
            exec_result = tool.execute(args)
        except Exception as exc:  # noqa: BLE001 - tools should not raise, but be safe
            exec_result = ToolResult.fail(f"Tool crashed: {exc}")

        self._log(user_text, plan, tool, preview, result.risk, confirmation, exec_result)
        status = "ok" if exec_result.success else "failed"
        self.cb.on_timeline(f"{tool.name} -> {status}: {exec_result.message}")
        self._feed_tool_result(call, exec_result)

    # -- helpers -------------------------------------------------------------
    def _feed_tool_result(self, call: ToolCall, result: ToolResult) -> None:
        payload = ("OK: " if result.success else "ERROR: ") + (result.message or "")
        if result.data:
            payload += f"\nData: {result.data}"
        self.memory.add_tool_result(payload, name=call.name, tool_call_id=call.id)

    def _exposed_tools(self, mode: AgentMode) -> list[BaseTool]:
        settings = self.safety.settings
        if mode == AgentMode.CHAT:
            return []
        return self.registry.available(
            automation_enabled=settings.automation_enabled,
            screen_enabled=settings.screen_access_enabled,
            browser_enabled=True,
        )

    def _finish_assistant(self, text: str) -> None:
        if text:
            self.memory.add_assistant(text)
            self.db.add_message(self.session_id, MessageRole.ASSISTANT, text)
            self.cb.on_assistant_message(text)
        self.cb.on_status(AgentStatus.IDLE)

    def _stop_message(self) -> str:
        self.cb.on_status(AgentStatus.IDLE)
        self.cb.on_timeline("Task cancelled by user (emergency stop).")
        msg = "Task cancelled."
        self.db.add_message(self.session_id, MessageRole.ASSISTANT, msg)
        self.cb.on_assistant_message(msg)
        return msg

    def _log(
        self,
        user_text: str,
        plan: str,
        tool: BaseTool,
        args_summary: str,
        risk: RiskLevel,
        confirmation: str,
        result: ToolResult,
    ) -> None:
        self.db.log_action(
            ActionLogEntry(
                session_id=self.session_id,
                user_request=user_text,
                plan=plan,
                tool_name=tool.name,
                tool_args_summary=args_summary,
                risk_level=risk,
                confirmation=confirmation,
                result=result.message if result.success else "",
                error="" if result.success else result.message,
                screenshot_meta=result.screenshot_meta,
            )
        )
