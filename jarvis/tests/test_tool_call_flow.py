"""Regression tests for the OpenAI tool-calling message order bug.

Bug: a ``role="tool"`` message was sent without a preceding assistant message
containing matching ``tool_calls``, causing OpenAI to reject the request with
"messages with role 'tool' must be a response to a preceding message with
'tool_calls'". These tests lock in the correct ordering and the orphan filter.
"""
from __future__ import annotations

from jarvis.agent.agent_loop import AgentCallbacks, AgentLoop
from jarvis.agent.memory import ConversationMemory
from jarvis.agent.safety import SafetyManager
from jarvis.app.settings import Settings
from jarvis.llm.base import LLMMessage, LLMProvider, LLMResponse, ToolCall
from jarvis.llm.openai_provider import sanitize_tool_messages, to_openai_messages
from jarvis.storage.models import AgentMode
from jarvis.tools.registry import build_default_registry


# --------------------------------------------------------------------------- #
# Pure serialization / sanitization tests
# --------------------------------------------------------------------------- #
def test_assistant_tool_calls_immediately_followed_by_tool_message():
    tc = ToolCall(id="call_1", name="list_directory", arguments={"path": "~/Desktop"})
    messages = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="list my desktop"),
        LLMMessage(role="assistant", content="", tool_calls=[tc]),
        LLMMessage(role="tool", content="OK: 3 entries", tool_call_id="call_1", name="list_directory"),
    ]
    payload = to_openai_messages(messages)

    # Find the assistant-with-tool_calls and assert the very next message is the
    # matching tool reply.
    idx = next(i for i, m in enumerate(payload) if m["role"] == "assistant" and m.get("tool_calls"))
    assert payload[idx]["tool_calls"][0]["id"] == "call_1"
    assert payload[idx]["tool_calls"][0]["function"]["name"] == "list_directory"
    nxt = payload[idx + 1]
    assert nxt["role"] == "tool"
    assert nxt["tool_call_id"] == "call_1"


def test_no_orphan_tool_messages_are_ever_sent():
    # A tool message with no preceding assistant tool_calls must be dropped.
    messages = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="hi"),
        LLMMessage(role="tool", content="orphan!", tool_call_id="ghost"),
    ]
    payload = to_openai_messages(messages)
    assert all(m["role"] != "tool" for m in payload)


def test_mismatched_tool_call_id_is_filtered():
    tc = ToolCall(id="call_A", name="list_directory", arguments={})
    messages = [
        LLMMessage(role="assistant", content="", tool_calls=[tc]),
        LLMMessage(role="tool", content="wrong id", tool_call_id="call_B"),
    ]
    payload = to_openai_messages(messages)
    assert all(m["role"] != "tool" for m in payload)


def test_sanitize_preserves_valid_pair_and_order():
    tc = ToolCall(id="x", name="t", arguments={})
    messages = [
        LLMMessage(role="user", content="u"),
        LLMMessage(role="assistant", content="", tool_calls=[tc]),
        LLMMessage(role="tool", content="r", tool_call_id="x"),
    ]
    cleaned = sanitize_tool_messages(messages)
    assert [m.role for m in cleaned] == ["user", "assistant", "tool"]


# --------------------------------------------------------------------------- #
# Agent-loop integration with a recording fake provider
# --------------------------------------------------------------------------- #
class RecordingProvider(LLMProvider):
    name = "rec"

    def __init__(self, scripted: list[LLMResponse]) -> None:
        super().__init__(model="rec")
        self._scripted = scripted
        self.received: list[list[LLMMessage]] = []

    def default_model(self) -> str:
        return "rec"

    def is_configured(self) -> bool:
        return True

    def chat(self, messages, tools=None, temperature: float = 0.2) -> LLMResponse:
        # Record a snapshot of exactly what the loop asked us to send.
        self.received.append(list(messages))
        return self._scripted.pop(0) if self._scripted else LLMResponse(text="(end)")


def _make_loop(db, provider):
    settings = Settings(agent_mode=AgentMode.CONTROLLED)
    session = db.create_session("test")
    return AgentLoop(
        provider=provider,
        registry=build_default_registry(),
        safety=SafetyManager(settings),
        memory=ConversationMemory(),
        db=db,
        session_id=session.id,
        callbacks=AgentCallbacks(),
    )


def test_list_directory_flow_produces_valid_message_order(db, tmp_path):
    (tmp_path / "a.txt").write_text("1")
    tc = ToolCall(id="call_1", name="list_directory", arguments={"path": str(tmp_path)})
    provider = RecordingProvider([
        LLMResponse(text="", tool_calls=[tc]),       # round 1: request the tool
        LLMResponse(text="Here are your files."),     # round 2: final answer
    ])
    loop = _make_loop(db, provider)
    out = loop.handle("List the files in my Desktop folder")
    assert out == "Here are your files."

    # The SECOND call must contain assistant.tool_calls immediately followed by
    # the matching tool message.
    second = provider.received[1]
    idx = next(i for i, m in enumerate(second)
               if m.role == "assistant" and m.tool_calls)
    assert second[idx].tool_calls[0].id == "call_1"
    assert second[idx + 1].role == "tool"
    assert second[idx + 1].tool_call_id == "call_1"

    # And that snapshot serializes to a valid OpenAI payload with no orphans.
    payload = to_openai_messages(second)
    for i, m in enumerate(payload):
        if m["role"] == "tool":
            prev = payload[i - 1]
            assert prev["role"] == "assistant" and prev.get("tool_calls")


def test_long_term_memory_has_no_tool_messages(db, tmp_path):
    tc = ToolCall(id="call_1", name="list_directory", arguments={"path": str(tmp_path)})
    provider = RecordingProvider([
        LLMResponse(text="", tool_calls=[tc]),
        LLMResponse(text="All done."),
    ])
    loop = _make_loop(db, provider)
    loop.handle("list things")

    msgs = loop.memory.build()
    roles = [m.role for m in msgs]
    # Only system/user/assistant survive in long-term memory - never tool, and
    # no assistant message should carry tool_calls.
    assert "tool" not in roles
    assert all(not (m.role == "assistant" and m.tool_calls) for m in msgs)
    assert msgs[-1].role == "assistant" and msgs[-1].content == "All done."


def test_preexisting_orphan_tool_message_is_filtered_before_api(db, tmp_path):
    # Simulate memory left dirty by an older buggy session.
    provider = RecordingProvider([LLMResponse(text="ok")])
    loop = _make_loop(db, provider)
    loop.memory._messages.append(
        LLMMessage(role="tool", content="leftover orphan", tool_call_id="old")
    )
    loop.handle("hello")

    # Whatever the loop sent, after sanitization it must contain no orphan tool.
    sent = provider.received[0]
    payload = to_openai_messages(sent)
    assert all(m["role"] != "tool" for m in payload)
