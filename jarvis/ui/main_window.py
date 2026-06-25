"""The JARVIS main window - the futuristic HUD console.

Layout:
  * Left column: radar, status indicator, capability toggles, stop button.
  * Centre: chat transcript + input + send/voice buttons.
  * Right column: action timeline and session-history access.

The agent runs on a background QThread so the UI never freezes. Confirmation
requests are marshalled back to the UI thread via a blocking signal, so the
modal dialog appears on the main thread while the worker waits for the answer.
"""
from __future__ import annotations

import threading
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..agent.agent_loop import (
    AgentCallbacks,
    AgentLoop,
    ConfirmDecision,
    ConfirmRequest,
)
from ..agent.memory import ConversationMemory
from ..agent.safety import SafetyManager
from ..app.settings import Settings
from ..llm.factory import get_provider
from ..storage.database import Database
from ..storage.models import AgentStatus, MessageRole
from ..tools.registry import build_default_registry
from .confirm_dialog import ConfirmationDialog
from .hud_widgets import RadarWidget, StatusIndicator, WaveformWidget
from .settings_dialog import SettingsDialog


class AgentWorker(QThread):
    """Runs a single agent request off the UI thread."""

    status_changed = Signal(object)       # AgentStatus
    timeline_added = Signal(str)
    assistant_message = Signal(str)
    confirm_needed = Signal(object)       # ConfirmRequest
    finished_request = Signal()

    def __init__(self, agent: AgentLoop, user_text: str) -> None:
        super().__init__()
        self.agent = agent
        self.user_text = user_text
        self._confirm_event = threading.Event()
        self._confirm_decision = ConfirmDecision.DENY
        # Wire the agent's callbacks to our signals.
        self.agent.cb = AgentCallbacks(
            on_status=lambda s: self.status_changed.emit(s),
            on_timeline=lambda t: self.timeline_added.emit(t),
            on_assistant_message=lambda m: self.assistant_message.emit(m),
            confirm=self._confirm,
        )

    def _confirm(self, request: ConfirmRequest) -> ConfirmDecision:
        """Called on the worker thread; blocks until the UI answers."""
        self._confirm_event.clear()
        self.confirm_needed.emit(request)
        self._confirm_event.wait()
        return self._confirm_decision

    def provide_confirmation(self, decision: ConfirmDecision) -> None:
        self._confirm_decision = decision
        self._confirm_event.set()

    def run(self) -> None:
        try:
            self.agent.handle(self.user_text)
        finally:
            self.finished_request.emit()


class MainWindow(QWidget):
    def __init__(self, db: Database, settings: Settings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.registry = build_default_registry()
        self.safety = SafetyManager(settings)
        self.memory = ConversationMemory()
        self.session = db.create_session("JARVIS session")
        self._worker: Optional[AgentWorker] = None

        self.setWindowTitle("JARVIS")
        self.setObjectName("RootBackground")
        self.resize(1180, 720)
        self._build_ui()
        self._install_shortcuts()
        self._refresh_provider_banner()

    # -- UI construction -----------------------------------------------------
    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        root.addWidget(self._build_left_panel(), 0)
        root.addWidget(self._build_center_panel(), 1)
        root.addWidget(self._build_right_panel(), 0)

    def _card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("GlassCard")
        return frame

    def _build_left_panel(self) -> QWidget:
        card = self._card()
        card.setFixedWidth(260)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("J A R V I S")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("ASSISTANT CONSOLE")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.radar = RadarWidget()
        layout.addWidget(self.radar, alignment=Qt.AlignCenter)

        self.status_indicator = StatusIndicator()
        layout.addWidget(self.status_indicator)

        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)

        layout.addSpacing(6)
        section = QLabel("CAPABILITIES")
        section.setObjectName("SectionLabel")
        layout.addWidget(section)

        self.screen_btn = QPushButton("Screen access: OFF")
        self.screen_btn.setObjectName("ToggleButton")
        self.screen_btn.setCheckable(True)
        self.screen_btn.setChecked(self.settings.screen_access_enabled)
        self.screen_btn.toggled.connect(self._toggle_screen)
        self._sync_toggle_text(self.screen_btn, "Screen access", self.settings.screen_access_enabled)
        layout.addWidget(self.screen_btn)

        self.automation_btn = QPushButton("Automation mode: OFF")
        self.automation_btn.setObjectName("ToggleButton")
        self.automation_btn.setCheckable(True)
        self.automation_btn.setChecked(self.settings.automation_enabled)
        self.automation_btn.toggled.connect(self._toggle_automation)
        self._sync_toggle_text(self.automation_btn, "Automation mode", self.settings.automation_enabled)
        layout.addWidget(self.automation_btn)

        layout.addStretch(1)

        self.stop_btn = QPushButton("■  STOP / CANCEL")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.clicked.connect(self._emergency_stop)
        layout.addWidget(self.stop_btn)

        self.settings_btn = QPushButton("⚙  Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self.settings_btn)

        return card

    def _build_center_panel(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.banner = QLabel("")
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet("color:#ffcf5f; font-size:12px;")
        layout.addWidget(self.banner)

        self.chat_view = QTextEdit()
        self.chat_view.setObjectName("ChatView")
        self.chat_view.setReadOnly(True)
        layout.addWidget(self.chat_view, 1)

        input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("Ask JARVIS to do something...  (Ctrl+Shift+J to focus)")
        self.chat_input.returnPressed.connect(self._on_send)
        input_row.addWidget(self.chat_input, 1)

        self.voice_btn = QPushButton("🎙")
        self.voice_btn.setToolTip("Push-to-talk (voice input is a stub until enabled in Settings)")
        self.voice_btn.clicked.connect(self._on_voice)
        input_row.addWidget(self.voice_btn)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendButton")
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)
        return card

    def _build_right_panel(self) -> QWidget:
        card = self._card()
        card.setFixedWidth(300)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        section = QLabel("ACTION TIMELINE")
        section.setObjectName("SectionLabel")
        layout.addWidget(section)

        self.timeline = QListWidget()
        layout.addWidget(self.timeline, 1)

        history_section = QLabel("SESSION HISTORY")
        history_section.setObjectName("SectionLabel")
        layout.addWidget(history_section)

        self.history_btn = QPushButton("View action log")
        self.history_btn.clicked.connect(self._show_history)
        layout.addWidget(self.history_btn)

        return card

    def _install_shortcuts(self) -> None:
        # In-app hotkey to focus the input. A truly global (OS-wide) hotkey
        # needs a platform helper on Windows; documented in the README.
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+J"), self)
        shortcut.activated.connect(self._focus_input)
        stop_shortcut = QShortcut(QKeySequence("Esc"), self)
        stop_shortcut.activated.connect(self._emergency_stop)

    # -- helpers -------------------------------------------------------------
    def _focus_input(self) -> None:
        self.raise_()
        self.activateWindow()
        self.chat_input.setFocus()

    def _sync_toggle_text(self, btn: QPushButton, label: str, on: bool) -> None:
        btn.setText(f"{label}: {'ON' if on else 'OFF'}")

    def _refresh_provider_banner(self) -> None:
        provider = get_provider(self.settings)
        if not provider.is_configured():
            self.banner.setText(
                f"No LLM configured for '{self.settings.llm_provider}'. Open "
                f"Settings to add an API key (or use Ollama locally). You can "
                f"still explore the HUD and the safety system."
            )
        else:
            self.banner.setText("")

    def _append_chat(self, role: str, text: str) -> None:
        colors = {"You": "#9fe0ff", "JARVIS": "#5fd2ff", "System": "#ffcf5f"}
        color = colors.get(role, "#cfe9ff")
        self.chat_view.append(
            f'<div style="margin:6px 0;"><b style="color:{color};">{role}:</b> '
            f'<span style="color:#d7ecff;">{text}</span></div>'
        )
        self.chat_view.verticalScrollBar().setValue(
            self.chat_view.verticalScrollBar().maximum()
        )

    # -- toggles -------------------------------------------------------------
    def _toggle_screen(self, checked: bool) -> None:
        self.settings.screen_access_enabled = checked
        self.settings.save(self.db)
        self._sync_toggle_text(self.screen_btn, "Screen access", checked)

    def _toggle_automation(self, checked: bool) -> None:
        if checked:
            confirm = QMessageBox.question(
                self,
                "Enable Automation mode?",
                "Automation mode lets JARVIS control your mouse and keyboard. "
                "High-risk actions still require confirmation. Enable it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm != QMessageBox.Yes:
                self.automation_btn.setChecked(False)
                return
        self.settings.automation_enabled = checked
        self.settings.save(self.db)
        self._sync_toggle_text(self.automation_btn, "Automation mode", checked)

    # -- sending -------------------------------------------------------------
    def _on_send(self) -> None:
        text = self.chat_input.text().strip()
        if not text or (self._worker and self._worker.isRunning()):
            return
        self.chat_input.clear()
        self._append_chat("You", text)
        self._set_busy(True)

        # Rebuild provider/safety from current settings for this request.
        provider = get_provider(self.settings)
        self.safety.settings = self.settings
        agent = AgentLoop(
            provider=provider,
            registry=self.registry,
            safety=self.safety,
            memory=self.memory,
            db=self.db,
            session_id=self.session.id,
        )
        worker = AgentWorker(agent, text)
        worker.status_changed.connect(self._on_status)
        worker.timeline_added.connect(self._on_timeline)
        worker.assistant_message.connect(lambda m: self._append_chat("JARVIS", m))
        worker.confirm_needed.connect(self._on_confirm_needed)
        worker.finished_request.connect(self._on_finished)
        self._worker = worker
        worker.start()

    def _on_voice(self) -> None:
        self._append_chat(
            "System",
            "Voice input is a stub in this build. Enable voice in Settings and "
            "install an STT backend (faster-whisper) to use push-to-talk.",
        )

    def _set_busy(self, busy: bool) -> None:
        self.send_btn.setEnabled(not busy)
        self.chat_input.setEnabled(not busy)
        self.radar.set_active(busy)
        self.waveform.set_active(busy)
        if not busy:
            self.chat_input.setFocus()

    # -- worker signal handlers (run on UI thread) ---------------------------
    def _on_status(self, status: AgentStatus) -> None:
        self.status_indicator.set_status(status)

    def _on_timeline(self, text: str) -> None:
        self.timeline.addItem(text)
        self.timeline.scrollToBottom()

    def _on_confirm_needed(self, request: ConfirmRequest) -> None:
        dialog = ConfirmationDialog(request, self)
        dialog.exec()
        if self._worker:
            self._worker.provide_confirmation(dialog.decision)

    def _on_finished(self) -> None:
        self._set_busy(False)
        self.status_indicator.set_status(AgentStatus.IDLE)

    def _emergency_stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.agent.request_stop()
            # If we're blocked waiting on a confirmation, deny it to unblock.
            self._worker.provide_confirmation(ConfirmDecision.DENY)
            self._on_timeline("Emergency stop requested.")

    # -- settings / history --------------------------------------------------
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = dialog.updated_settings()
            self.settings.save(self.db)
            self.safety.settings = self.settings
            self._sync_toggle_text(self.screen_btn, "Screen access", self.settings.screen_access_enabled)
            self.screen_btn.setChecked(self.settings.screen_access_enabled)
            self._sync_toggle_text(self.automation_btn, "Automation mode", self.settings.automation_enabled)
            self.automation_btn.setChecked(self.settings.automation_enabled)
            self._refresh_provider_banner()

    def _show_history(self) -> None:
        entries = self.db.get_action_log(limit=200)
        if not entries:
            QMessageBox.information(self, "Session History", "No actions logged yet.")
            return
        lines = []
        for e in entries:
            stamp = e.created_at.strftime("%Y-%m-%d %H:%M:%S")
            outcome = e.error or e.result or "(no result)"
            lines.append(
                f"[{stamp}] {e.tool_name} ({e.risk_level.value}, {e.confirmation}): {outcome}"
            )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Session History - Action Log")
        dlg.setText("\n".join(lines[:60]))
        dlg.exec()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._worker and self._worker.isRunning():
            self._worker.agent.request_stop()
            self._worker.provide_confirmation(ConfirmDecision.DENY)
            self._worker.wait(2000)
        event.accept()
