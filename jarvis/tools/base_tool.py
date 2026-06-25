"""Base classes for tools.

Every tool declares:
  * name / description
  * an ``InputModel`` (a pydantic model) describing its arguments
  * a static ``risk_level`` and ``requires_confirmation`` flag
  * ``dynamic_risk(args)`` to escalate risk based on actual arguments
  * ``preview(args)`` -> a human-readable description shown before execution
  * ``execute(args)`` -> a ``ToolResult``

Tools must NEVER perform a side effect inside ``preview``. The agent loop calls
``preview`` (and the safety layer) before it ever calls ``execute``.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError

from ..storage.models import RiskLevel


@dataclass
class ToolResult:
    """The outcome of executing a tool."""

    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    # Optional screenshot metadata (never raw bytes) for the action log.
    screenshot_meta: Optional[str] = None

    @classmethod
    def ok(cls, message: str = "", **data: Any) -> "ToolResult":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, **data: Any) -> "ToolResult":
        return cls(success=False, message=message, data=data)


class EmptyArgs(BaseModel):
    """Default input model for tools that take no arguments."""


class BaseTool(abc.ABC):
    """Abstract base class for all tools."""

    name: str = "base_tool"
    description: str = ""
    InputModel: Type[BaseModel] = EmptyArgs
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    # Marks tools whose risk is so high that "always allow for session" is
    # disallowed - only a one-time "Allow once" is offered.
    extreme_risk: bool = False
    # Capability this tool depends on; the registry can hide tools whose
    # capability is disabled. One of: None | "automation" | "screen" | "browser".
    capability: Optional[str] = None

    def validate_args(self, raw: dict[str, Any]) -> BaseModel:
        """Validate raw args against the input model (raises ValidationError)."""
        return self.InputModel(**(raw or {}))

    def dynamic_risk(self, args: BaseModel) -> RiskLevel:
        """Risk for the specific call. Override to escalate based on args."""
        return self.risk_level

    @abc.abstractmethod
    def preview(self, args: BaseModel) -> str:
        """Return a human-readable description of what execution will do."""

    @abc.abstractmethod
    def execute(self, args: BaseModel) -> ToolResult:
        """Perform the action. Should not raise for expected failures."""

    # -- schema for the LLM --------------------------------------------------
    def to_schema(self) -> dict[str, Any]:
        """Return an OpenAI-style function/tool schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.InputModel.model_json_schema(),
            },
        }

    def safe_validate(self, raw: dict[str, Any]) -> tuple[Optional[BaseModel], Optional[str]]:
        """Validate args, returning (model, None) or (None, error_message)."""
        try:
            return self.validate_args(raw), None
        except ValidationError as exc:
            return None, f"Invalid arguments for '{self.name}': {exc}"
