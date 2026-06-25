"""Confirmation dialog shown before medium/high-risk actions.

Displays what the agent wants to do, why, and the exact data being changed,
with buttons: Allow once / Deny / Always allow (this session). For extreme-risk
actions, "Always allow" is suppressed - only "Allow once" is offered.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..agent.agent_loop import ConfirmDecision, ConfirmRequest
from ..storage.models import RiskLevel

_RISK_COLORS = {
    RiskLevel.LOW: "#43e0a0",
    RiskLevel.MEDIUM: "#ffcf5f",
    RiskLevel.HIGH: "#ff9f43",
    RiskLevel.BLOCKED: "#ff5a6e",
}


class ConfirmationDialog(QDialog):
    def __init__(self, request: ConfirmRequest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("JARVIS - Confirmation required")
        self.setModal(True)
        self.setMinimumWidth(460)
        self._decision = ConfirmDecision.DENY

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        color = _RISK_COLORS.get(request.risk, "#ffcf5f")
        header = QLabel(f"● {request.risk.value.upper()} RISK ACTION")
        header.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 700; letter-spacing: 2px;")
        layout.addWidget(header)

        tool_label = QLabel(f"Tool: <b>{request.tool_name}</b>")
        tool_label.setTextFormat(Qt.RichText)
        layout.addWidget(tool_label)

        what = QLabel("What it will do:")
        what.setStyleSheet("color:#4fb8e6; font-weight:600;")
        layout.addWidget(what)

        detail = QTextEdit()
        detail.setReadOnly(True)
        detail.setPlainText(request.preview)
        detail.setMaximumHeight(140)
        layout.addWidget(detail)

        if request.why:
            why = QLabel(f"Why / how classified: {request.why}")
            why.setWordWrap(True)
            why.setStyleSheet("color:#6c8bab; font-size:11px;")
            layout.addWidget(why)

        # Buttons.
        buttons = QHBoxLayout()
        deny_btn = QPushButton("Deny")
        deny_btn.clicked.connect(self._deny)
        buttons.addWidget(deny_btn)

        buttons.addStretch(1)

        if not request.allow_once_only:
            always_btn = QPushButton("Always allow (session)")
            always_btn.clicked.connect(self._always)
            buttons.addWidget(always_btn)

        allow_btn = QPushButton("Allow once")
        allow_btn.setObjectName("SendButton")
        allow_btn.clicked.connect(self._allow_once)
        allow_btn.setDefault(True)
        buttons.addWidget(allow_btn)

        layout.addLayout(buttons)

    # -- result --------------------------------------------------------------
    def _allow_once(self) -> None:
        self._decision = ConfirmDecision.ALLOW_ONCE
        self.accept()

    def _always(self) -> None:
        self._decision = ConfirmDecision.ALWAYS
        self.accept()

    def _deny(self) -> None:
        self._decision = ConfirmDecision.DENY
        self.reject()

    @property
    def decision(self) -> ConfirmDecision:
        return self._decision
