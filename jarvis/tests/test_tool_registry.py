"""Tests for the tool registry: registration, schemas, capability filtering."""
from __future__ import annotations

import pytest

from jarvis.storage.models import RiskLevel
from jarvis.tools.file_tools import WriteTextFileTool
from jarvis.tools.registry import ToolRegistry, build_default_registry


def test_register_and_lookup():
    reg = ToolRegistry()
    tool = WriteTextFileTool()
    reg.register(tool)
    assert reg.has("write_text_file")
    assert reg.get("write_text_file") is tool


def test_duplicate_registration_raises():
    reg = ToolRegistry()
    reg.register(WriteTextFileTool())
    with pytest.raises(ValueError):
        reg.register(WriteTextFileTool())


def test_default_registry_has_expected_tools():
    reg = build_default_registry()
    names = {t.name for t in reg.all()}
    for expected in [
        "open_app", "close_app", "focus_window", "list_open_windows",
        "search_files", "read_text_file", "write_text_file", "delete_file",
        "open_url", "search_web", "screenshot_screen", "click",
        "send_email", "create_event",
    ]:
        assert expected in names


def test_schema_generation_is_valid_shape():
    reg = build_default_registry()
    schemas = reg.schemas()
    assert schemas, "expected non-empty schema list"
    for schema in schemas:
        assert schema["type"] == "function"
        fn = schema["function"]
        assert "name" in fn and "description" in fn
        assert fn["parameters"]["type"] == "object"


def test_dynamic_risk_overwrite_is_high(tmp_path):
    tool = WriteTextFileTool()
    existing = tmp_path / "exists.txt"
    existing.write_text("old")
    args = tool.validate_args({"path": str(existing), "content": "new"})
    assert tool.dynamic_risk(args) == RiskLevel.HIGH

    new_args = tool.validate_args({"path": str(tmp_path / "fresh.txt"), "content": "x"})
    assert tool.dynamic_risk(new_args) == RiskLevel.MEDIUM


def test_capability_filtering_hides_desktop_tools_by_default():
    reg = build_default_registry()
    available = reg.available(automation_enabled=False, screen_enabled=False)
    names = {t.name for t in available}
    # Desktop automation tools require the 'automation'/'screen' capability.
    assert "click" not in names
    assert "type_text" not in names
    assert "screenshot_screen" not in names
    # File/app tools remain available.
    assert "search_files" in names
    assert "open_app" in names


def test_capability_filtering_reveals_desktop_tools_when_enabled():
    reg = build_default_registry()
    available = reg.available(automation_enabled=True, screen_enabled=True)
    names = {t.name for t in available}
    assert "click" in names
    assert "screenshot_screen" in names
