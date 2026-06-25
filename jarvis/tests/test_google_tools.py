"""Tests for Phase 6 Gmail/Calendar tools: registration, risk, graceful setup."""
from __future__ import annotations

from jarvis.agent.safety import SafetyDecision, SafetyManager
from jarvis.app.settings import Settings
from jarvis.storage.models import AgentMode, RiskLevel
from jarvis.tools.calendar_tools import (
    CreateEventTool,
    DeleteEventTool,
    build_calendar_tools,
)
from jarvis.tools.email_tools import (
    CountSentEmailsTool,
    SendEmailTool,
    build_email_tools,
)
from jarvis.tools.google_client import GoogleClient, google_libs_available
from jarvis.tools.registry import build_default_registry


def _mgr() -> SafetyManager:
    return SafetyManager(Settings(agent_mode=AgentMode.CONTROLLED))


def test_email_and_calendar_tools_registered():
    names = {t.name for t in build_default_registry().all()}
    for n in ["count_sent_emails", "search_emails", "summarize_emails",
              "draft_email", "send_email", "list_events", "find_free_slots",
              "create_event", "delete_event"]:
        assert n in names


def test_google_libs_available_returns_bool():
    assert isinstance(google_libs_available(), bool)


def test_tools_without_google_return_setup_message():
    # Google libs / credentials are absent in CI -> a clear setup message.
    tool = CountSentEmailsTool()
    res = tool.execute(tool.validate_args({"time_range": "this week"}))
    assert res.success is False
    assert "google" in res.message.lower() or "gmail" in res.message.lower()


def test_send_email_is_extreme_risk_allow_once():
    mgr = _mgr()
    tool = SendEmailTool()
    args = tool.validate_args({"to": "a@b.com", "subject": "hi", "body": "hello"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.risk == RiskLevel.HIGH
    assert result.allow_once_only is True


def test_create_event_requires_confirmation():
    mgr = _mgr()
    tool = CreateEventTool()
    args = tool.validate_args({"title": "Sync", "start": "2026-07-01T10:00:00",
                               "end": "2026-07-01T11:00:00"})
    assert mgr.evaluate(tool, args).decision == SafetyDecision.CONFIRM


def test_delete_event_is_extreme_allow_once():
    assert DeleteEventTool().extreme_risk is True
    assert DeleteEventTool().requires_confirmation is True


def test_send_email_requires_confirmation_flag():
    assert SendEmailTool().requires_confirmation is True
    assert SendEmailTool().extreme_risk is True


def test_setup_message_is_actionable():
    msg = GoogleClient().setup_message()
    assert "credentials" in msg.lower() or "pip install" in msg.lower()
