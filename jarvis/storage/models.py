"""Pydantic models that mirror the persisted database rows and shared enums.

These are intentionally light data-transfer objects. They keep the rest of the
codebase decoupled from raw SQLite tuples and give us validation + typing.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RiskLevel(str, enum.Enum):
    """Risk classification for an action. Ordered low -> blocked."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"

    @property
    def order(self) -> int:
        return {"low": 0, "medium": 1, "high": 2, "blocked": 3}[self.value]


class AgentMode(str, enum.Enum):
    """Operating mode for the agent (how much it is allowed to do)."""

    CHAT = "chat"            # only talks
    ASSIST = "assist"        # may suggest actions, never executes
    CONTROLLED = "controlled"  # executes low-risk actions, confirms the rest
    CONFIRMATION = "confirmation"  # confirms before any action with side effects


class AgentStatus(str, enum.Enum):
    """High-level status surfaced in the HUD status panel."""

    IDLE = "Idle"
    LISTENING = "Listening"
    TRANSCRIBING = "Transcribing"
    THINKING = "Thinking"
    ACTING = "Acting"
    SPEAKING = "Speaking"
    NEEDS_CONFIRMATION = "Needs confirmation"
    ERROR = "Error"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single conversation message."""

    id: Optional[int] = None
    session_id: int
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=_utcnow)


class Session(BaseModel):
    id: Optional[int] = None
    title: str = "Session"
    created_at: datetime = Field(default_factory=_utcnow)


class ActionLogEntry(BaseModel):
    """One row in the action log - the audit trail of agent behaviour."""

    id: Optional[int] = None
    session_id: int
    created_at: datetime = Field(default_factory=_utcnow)
    user_request: str = ""
    plan: str = ""
    tool_name: str = ""
    tool_args_summary: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    confirmation: str = ""      # e.g. "not required", "allow_once", "denied"
    result: str = ""
    error: str = ""
    # Screenshot metadata only (path/dims/size); never the raw image unless the
    # user explicitly enables screenshot logging.
    screenshot_meta: Optional[str] = None


class SettingsRow(BaseModel):
    """Generic key/value settings row."""

    key: str
    value: Any
