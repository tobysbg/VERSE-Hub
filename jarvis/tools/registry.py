"""Tool registry: registration, lookup, schema export, capability filtering."""
from __future__ import annotations

from typing import Iterable, Optional

from .base_tool import BaseTool


class ToolRegistry:
    """Holds the set of available tools and filters them by enabled capabilities."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def register_all(self, tools: Iterable[BaseTool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def available(
        self,
        *,
        automation_enabled: bool = False,
        screen_enabled: bool = False,
        browser_enabled: bool = True,
    ) -> list[BaseTool]:
        """Return only the tools whose capability requirement is satisfied."""
        enabled = {
            "automation": automation_enabled,
            "screen": screen_enabled,
            "browser": browser_enabled,
            None: True,
        }
        return [t for t in self._tools.values() if enabled.get(t.capability, True)]

    def schemas(self, tools: Optional[list[BaseTool]] = None) -> list[dict]:
        """Export OpenAI-style schemas for the given (or all) tools."""
        selected = tools if tools is not None else self.all()
        return [t.to_schema() for t in selected]


def build_default_registry() -> "ToolRegistry":
    """Construct a registry populated with every built-in tool.

    Imports are local to avoid import cycles (tool modules import base_tool,
    which this module also imports).
    """
    from .app_tools import build_app_tools
    from .browser_tools import build_browser_tools
    from .calendar_tools import build_calendar_tools
    from .desktop_tools import build_desktop_tools
    from .email_tools import build_email_tools
    from .file_tools import build_file_tools

    registry = ToolRegistry()
    registry.register_all(build_app_tools())
    registry.register_all(build_file_tools())
    registry.register_all(build_browser_tools())
    registry.register_all(build_desktop_tools())
    registry.register_all(build_email_tools())
    registry.register_all(build_calendar_tools())
    return registry
