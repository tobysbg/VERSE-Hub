"""The safety layer - evaluated before every tool call.

Given a tool, its validated arguments, and the current settings, this module
decides one of:
  * ALLOW   - run it, no confirmation needed
  * CONFIRM - show a confirmation dialog first
  * BLOCK   - refuse (optionally explaining how to enable in developer mode)

Risk is the maximum of:
  * the tool's declared (possibly dynamic) risk level, and
  * heuristics over the arguments (payments, passwords, 2FA, bulk delete...).

This is the single most safety-critical module and is heavily unit-tested.
"""
from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel

from ..app.settings import Settings
from ..storage.models import AgentMode, RiskLevel
from ..tools.base_tool import BaseTool


class SafetyDecision(str, enum.Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    BLOCK = "block"


# Patterns that indicate the "blocked" categories from the spec. If any of these
# match the argument text, the action is blocked unless developer mode is on.
_BLOCKED_PATTERNS: dict[str, re.Pattern] = {
    "password": re.compile(r"\b(pass\s*word|passwd|pwd)\b", re.I),
    "2fa / one-time code": re.compile(r"\b(2fa|otp|one[\s-]?time\s+code|verification\s+code|auth(?:enticator)?\s+code)\b", re.I),
    "banking / payment credentials": re.compile(r"\b(bank|iban|routing\s+number|sort\s+code|cvv|card\s*number|credit\s*card)\b", re.I),
    "financial trade": re.compile(r"\b(buy|sell)\s+\d+\s+(shares|stock|crypto|btc|eth)\b", re.I),
    "credential scraping": re.compile(r"\b(scrape|dump|harvest)\s+(credential|password|cookie|token)s?\b", re.I),
    "security bypass": re.compile(r"\b(bypass|disable)\s+(antivirus|firewall|defender|security|captcha)\b", re.I),
    "keylogging / persistence": re.compile(r"\b(keylog|keystroke\s+log|persistence|autostart\s+stealth|hide\s+from\s+user)\b", re.I),
}

# Patterns that escalate to HIGH risk (sensitive but not outright blocked).
_HIGH_RISK_PATTERNS: dict[str, re.Pattern] = {
    "payment / purchase": re.compile(r"\b(pay|payment|checkout|purchase|order\s+now|place\s+order|book\s+now)\b", re.I),
    "personal identifiers": re.compile(r"\b(ssn|social\s+security|passport\s+number|national\s+id)\b", re.I),
    "bulk file operation": re.compile(r"\b(all|every|entire|\*)\b.*\b(file|files|folder|directory|downloads)\b", re.I),
}


@dataclass
class SafetyResult:
    decision: SafetyDecision
    risk: RiskLevel
    reasons: list[str] = field(default_factory=list)
    # When True, the confirmation dialog must NOT offer "always allow".
    allow_once_only: bool = False
    # A short message to show the user when blocked.
    block_message: str = ""


class SafetyManager:
    """Evaluates tool calls and tracks session-scoped 'always allow' grants."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Tool names the user chose "always allow this session" for.
        self._session_grants: set[str] = set()

    # -- session grants ------------------------------------------------------
    def grant_session(self, tool_name: str) -> None:
        self._session_grants.add(tool_name)

    def has_session_grant(self, tool_name: str) -> bool:
        return tool_name in self._session_grants

    def clear_session_grants(self) -> None:
        self._session_grants.clear()

    # -- core evaluation -----------------------------------------------------
    def assess_risk(self, tool: BaseTool, args: BaseModel) -> tuple[RiskLevel, list[str]]:
        """Return the effective risk level and the reasons that drove it."""
        reasons: list[str] = []
        risk = tool.dynamic_risk(args)
        if risk == tool.risk_level:
            reasons.append(f"{tool.name} base risk: {risk.value}")
        else:
            reasons.append(f"{tool.name} dynamic risk: {risk.value}")

        blob = self._args_text(args)

        for label, pattern in _BLOCKED_PATTERNS.items():
            if pattern.search(blob):
                reasons.append(f"matched blocked category: {label}")
                risk = RiskLevel.BLOCKED
        if risk == RiskLevel.BLOCKED:
            return risk, reasons

        for label, pattern in _HIGH_RISK_PATTERNS.items():
            if pattern.search(blob):
                reasons.append(f"matched high-risk pattern: {label}")
                if risk.order < RiskLevel.HIGH.order:
                    risk = RiskLevel.HIGH
        return risk, reasons

    def evaluate(self, tool: BaseTool, args: BaseModel) -> SafetyResult:
        risk, reasons = self.assess_risk(tool, args)
        mode = self.settings.agent_mode

        # --- BLOCKED category -------------------------------------------------
        if risk == RiskLevel.BLOCKED:
            if not self.settings.developer_mode:
                return SafetyResult(
                    decision=SafetyDecision.BLOCK,
                    risk=risk,
                    reasons=reasons,
                    block_message=(
                        "This action falls into a blocked category (passwords, "
                        "2FA, banking, security bypass, credential scraping, or "
                        "persistence). It is refused. If you genuinely need it, "
                        "enable Developer mode in Settings - and even then it "
                        "still requires one-time confirmation."
                    ),
                )
            # Developer mode: allow but force a one-time confirmation.
            return SafetyResult(
                decision=SafetyDecision.CONFIRM,
                risk=risk,
                reasons=reasons,
                allow_once_only=True,
            )

        # --- Assist mode never executes side effects -------------------------
        if mode == AgentMode.ASSIST and (risk.order >= RiskLevel.MEDIUM.order or tool.requires_confirmation):
            return SafetyResult(
                decision=SafetyDecision.BLOCK,
                risk=risk,
                reasons=reasons + ["assist mode does not execute actions"],
                block_message=(
                    "JARVIS is in Assist mode and will not execute actions. "
                    "Switch to Controlled or Confirmation mode to allow it."
                ),
            )

        # --- Decide on confirmation ------------------------------------------
        needs_confirm = tool.requires_confirmation or risk.order >= RiskLevel.MEDIUM.order
        allow_once_only = tool.extreme_risk or risk == RiskLevel.HIGH

        if not needs_confirm:
            return SafetyResult(SafetyDecision.ALLOW, risk, reasons)

        # Session "always allow" only applies to non-extreme actions.
        if not allow_once_only and self.has_session_grant(tool.name):
            return SafetyResult(
                SafetyDecision.ALLOW, risk, reasons + ["session grant for this tool"]
            )

        return SafetyResult(
            decision=SafetyDecision.CONFIRM,
            risk=risk,
            reasons=reasons,
            allow_once_only=allow_once_only,
        )

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _args_text(args: BaseModel) -> str:
        try:
            values = args.model_dump()
        except Exception:  # noqa: BLE001
            return ""
        parts: list[str] = []
        for v in values.values():
            if isinstance(v, (list, tuple)):
                parts.extend(str(x) for x in v)
            else:
                parts.append(str(v))
        return " ".join(parts)
