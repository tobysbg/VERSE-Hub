"""Tests for Phase 4 browser tools and their safety classification.

The live Playwright browser can't run in CI, so these tests cover the parts that
matter for safety and graceful degradation: setup messages when Playwright is
missing, submission-aware risk escalation, and that the safety manager blocks
passwords / banking and confirms payments.
"""
from __future__ import annotations

from jarvis.agent.safety import SafetyDecision, SafetyManager
from jarvis.app.settings import Settings
from jarvis.storage.models import AgentMode, RiskLevel
from jarvis.tools.browser_tools import (
    ClickTextTool,
    FillFieldTool,
    OpenUrlTool,
    build_browser_tools,
)
from jarvis.tools.registry import build_default_registry


def _mgr() -> SafetyManager:
    return SafetyManager(Settings(agent_mode=AgentMode.CONTROLLED))


def test_browser_tools_registered():
    reg = build_default_registry()
    names = {t.name for t in reg.all()}
    for n in ["open_url", "search_web", "click_text", "fill_field",
              "extract_page_text", "screenshot_page", "close_browser"]:
        assert n in names


def test_browser_tools_have_browser_capability():
    for tool in build_browser_tools():
        assert tool.capability == "browser"


def test_open_url_without_playwright_returns_setup_message():
    # Playwright is not installed in CI -> a clear setup hint, never a crash.
    tool = OpenUrlTool()
    res = tool.execute(tool.validate_args({"url": "example.com"}))
    assert res.success is False
    assert "playwright" in res.message.lower()


def test_click_submit_text_is_high_risk():
    tool = ClickTextTool()
    high = tool.validate_args({"text": "Place order"})
    assert tool.dynamic_risk(high) == RiskLevel.HIGH
    low = tool.validate_args({"text": "Show more results"})
    assert tool.dynamic_risk(low) == RiskLevel.MEDIUM


def test_click_payment_requires_confirmation_allow_once():
    mgr = _mgr()
    tool = ClickTextTool()
    args = tool.validate_args({"text": "Pay now"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.risk == RiskLevel.HIGH
    assert result.allow_once_only is True


def test_fill_field_with_password_is_blocked():
    mgr = _mgr()
    tool = FillFieldTool()
    args = tool.validate_args({"label_or_selector": "password", "value": "hunter2"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.BLOCK
    assert result.risk == RiskLevel.BLOCKED


def test_open_banking_url_is_blocked_without_dev_mode():
    mgr = _mgr()
    tool = OpenUrlTool()
    args = tool.validate_args({"url": "https://bank.example.com/login"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.BLOCK


def test_normal_click_requires_confirmation():
    mgr = _mgr()
    tool = ClickTextTool()
    args = tool.validate_args({"text": "Read the article"})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
