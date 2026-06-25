"""Tests for Phase 5 desktop control: gating, risk, and graceful degradation."""
from __future__ import annotations

from jarvis.agent.safety import SafetyDecision, SafetyManager
from jarvis.app.settings import Settings
from jarvis.storage.models import AgentMode, RiskLevel
from jarvis.tools.desktop_tools import (
    ClickTool,
    HotkeyTool,
    ScrollTool,
    TypeTextTool,
    build_desktop_tools,
)
from jarvis.tools.registry import build_default_registry


def _mgr() -> SafetyManager:
    return SafetyManager(Settings(agent_mode=AgentMode.CONTROLLED))


def test_desktop_tools_require_correct_capabilities():
    caps = {t.name: t.capability for t in build_desktop_tools()}
    assert caps["click"] == "automation"
    assert caps["type_text"] == "automation"
    assert caps["hotkey"] == "automation"
    assert caps["scroll"] == "automation"
    assert caps["screenshot_screen"] == "screen"
    assert caps["locate_text_on_screen"] == "screen"


def test_desktop_tools_hidden_unless_automation_enabled():
    reg = build_default_registry()
    off = {t.name for t in reg.available(automation_enabled=False, screen_enabled=False)}
    assert "click" not in off and "type_text" not in off and "screenshot_screen" not in off

    on = {t.name for t in reg.available(automation_enabled=True, screen_enabled=True)}
    assert "click" in on and "type_text" in on and "screenshot_screen" in on


def test_click_is_high_risk_confirm_allow_once():
    mgr = _mgr()
    tool = ClickTool()
    args = tool.validate_args({"x": 10, "y": 20})
    result = mgr.evaluate(tool, args)
    assert result.decision == SafetyDecision.CONFIRM
    assert result.risk == RiskLevel.HIGH
    assert result.allow_once_only is True


def test_type_and_hotkey_require_confirmation():
    assert TypeTextTool().requires_confirmation is True
    assert HotkeyTool().requires_confirmation is True


def test_scroll_is_low_risk():
    assert ScrollTool().risk_level == RiskLevel.LOW


def test_desktop_actions_without_backend_return_setup_message():
    # No pyautogui / no display in CI -> a clear setup message, never a crash.
    tool = ClickTool()
    res = tool.execute(tool.validate_args({"x": 1, "y": 1}))
    assert res.success is False
    assert "pyautogui" in res.message.lower() or "automation" in res.message.lower()


def test_automation_disabled_by_default():
    s = Settings()
    assert s.automation_enabled is False
    assert s.screen_access_enabled is False
