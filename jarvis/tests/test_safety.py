"""Tests for the safety classification layer - the most critical module."""
from __future__ import annotations

import pytest

from jarvis.agent.safety import SafetyDecision, SafetyManager
from jarvis.app.settings import Settings
from jarvis.storage.models import AgentMode, RiskLevel
from jarvis.tools.file_tools import (
    DeleteFileTool,
    ReadTextFileTool,
    SearchFilesTool,
    WriteTextFileTool,
)
from jarvis.tools.email_tools import SendEmailTool


def _mgr(**kwargs) -> SafetyManager:
    base = dict(agent_mode=AgentMode.CONTROLLED)
    base.update(kwargs)
    return SafetyManager(Settings(**base))


def test_low_risk_read_is_allowed():
    mgr = _mgr()
    tool = ReadTextFileTool()
    args = tool.validate_args({"path": "/tmp/x.txt"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.ALLOW
    assert result.risk == RiskLevel.LOW


def test_search_low_risk_allowed():
    mgr = _mgr()
    tool = SearchFilesTool()
    args = tool.validate_args({"query": "report", "folder": "/tmp"})
    assert mgr.evaluate(tool, args).decision == SafetyDecision.ALLOW


def test_write_new_file_requires_confirmation():
    mgr = _mgr()
    tool = WriteTextFileTool()
    args = tool.validate_args({"path": "/tmp/does-not-exist-xyz.txt", "content": "hi"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM


def test_delete_is_high_and_allow_once_only():
    mgr = _mgr()
    tool = DeleteFileTool()
    args = tool.validate_args({"path": "/tmp/whatever.txt"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.risk == RiskLevel.HIGH
    assert result.allow_once_only is True  # never "always allow"


def test_password_argument_is_blocked_without_dev_mode():
    mgr = _mgr()
    tool = WriteTextFileTool()
    args = tool.validate_args({"path": "/tmp/login.txt", "content": "my password is hunter2"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.BLOCK
    assert result.risk == RiskLevel.BLOCKED


def test_blocked_category_allowed_but_confirmed_in_dev_mode():
    mgr = _mgr(developer_mode=True)
    tool = WriteTextFileTool()
    args = tool.validate_args({"path": "/tmp/login.txt", "content": "the password is secret"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.allow_once_only is True


def test_bulk_delete_phrase_escalates_to_high():
    mgr = _mgr()
    tool = SearchFilesTool()  # low risk tool...
    args = tool.validate_args({"query": "delete all files in downloads", "folder": "/tmp"})
    risk, _ = mgr.assess_risk(tool, args)
    assert risk == RiskLevel.HIGH


def test_send_email_extreme_risk_allow_once_only():
    mgr = _mgr()
    tool = SendEmailTool()
    args = tool.validate_args({"to": "a@b.com", "subject": "hi", "body": "hello"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.allow_once_only is True


def test_assist_mode_blocks_side_effects():
    mgr = _mgr(agent_mode=AgentMode.ASSIST)
    tool = WriteTextFileTool()
    args = tool.validate_args({"path": "/tmp/new.txt", "content": "x"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.BLOCK


def test_session_grant_allows_medium_without_confirm():
    mgr = _mgr()
    tool = WriteTextFileTool()
    args = tool.validate_args({"path": "/tmp/brand-new-file-abc.txt", "content": "x"})
    # First time: confirm. Then grant for session.
    assert mgr.evaluate(tool, args).decision == SafetyDecision.CONFIRM
    mgr.grant_session(tool.name)
    assert mgr.evaluate(tool, args).decision == SafetyDecision.ALLOW


def test_session_grant_does_not_bypass_high_risk():
    mgr = _mgr()
    tool = DeleteFileTool()
    args = tool.validate_args({"path": "/tmp/file.txt"})
    mgr.grant_session(tool.name)
    # Still confirms because delete is allow-once-only.
    assert mgr.evaluate(tool, args).decision == SafetyDecision.CONFIRM
