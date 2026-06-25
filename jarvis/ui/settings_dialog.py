"""Settings dialog: providers/keys, voice, capability toggles, developer mode."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..app.settings import Settings
from ..storage.models import AgentMode


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("JARVIS - Settings")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._settings = settings

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # --- LLM ------------------------------------------------------------
        self.provider_box = QComboBox()
        self.provider_box.addItems(["openai", "anthropic", "ollama"])
        self.provider_box.setCurrentText(settings.llm_provider)
        form.addRow("LLM provider", self.provider_box)

        self.model_edit = QLineEdit(settings.llm_model)
        self.model_edit.setPlaceholderText("(blank = provider default)")
        form.addRow("Model", self.model_edit)

        self.openai_key = QLineEdit(settings.openai_api_key or "")
        self.openai_key.setEchoMode(QLineEdit.Password)
        form.addRow("OpenAI API key", self.openai_key)

        self.anthropic_key = QLineEdit(settings.anthropic_api_key or "")
        self.anthropic_key.setEchoMode(QLineEdit.Password)
        form.addRow("Anthropic API key", self.anthropic_key)

        self.ollama_url = QLineEdit(settings.ollama_base_url)
        form.addRow("Ollama base URL", self.ollama_url)

        self.mode_box = QComboBox()
        self.mode_box.addItems([m.value for m in AgentMode])
        self.mode_box.setCurrentText(settings.agent_mode.value)
        form.addRow("Agent mode", self.mode_box)

        # --- Voice ----------------------------------------------------------
        self.voice_enabled = QCheckBox("Enable voice")
        self.voice_enabled.setChecked(settings.voice_enabled)
        form.addRow(self.voice_enabled)

        self.stt_box = QComboBox()
        self.stt_box.addItems(["openai-whisper", "disabled"])
        self.stt_box.setCurrentText(settings.stt_provider)
        form.addRow("STT provider", self.stt_box)

        self.tts_box = QComboBox()
        self.tts_box.addItems(["pyttsx3", "disabled"])
        self.tts_box.setCurrentText(settings.tts_provider)
        form.addRow("TTS provider", self.tts_box)

        self.voice_speed = QDoubleSpinBox()
        self.voice_speed.setRange(0.5, 2.0)
        self.voice_speed.setSingleStep(0.1)
        self.voice_speed.setValue(settings.voice_speed)
        form.addRow("Voice speed", self.voice_speed)

        self.voice_autosend = QCheckBox("Auto-send transcription (otherwise fills the input)")
        self.voice_autosend.setChecked(settings.voice_autosend)
        form.addRow(self.voice_autosend)

        layout.addLayout(form)

        # --- Capability toggles --------------------------------------------
        caution = QLabel(
            "Capability toggles (default OFF for safety). Desktop automation can "
            "control your mouse and keyboard - enable only when you intend to use it."
        )
        caution.setWordWrap(True)
        caution.setStyleSheet("color:#6c8bab; font-size:11px;")
        layout.addWidget(caution)

        self.screen_toggle = QCheckBox("Screen access enabled")
        self.screen_toggle.setChecked(settings.screen_access_enabled)
        layout.addWidget(self.screen_toggle)

        self.automation_toggle = QCheckBox("Automation mode enabled (mouse/keyboard control)")
        self.automation_toggle.setChecked(settings.automation_enabled)
        layout.addWidget(self.automation_toggle)

        self.screenshot_log = QCheckBox("Save raw screenshots to logs (off = metadata only)")
        self.screenshot_log.setChecked(settings.screenshot_logging)
        layout.addWidget(self.screenshot_log)

        self.developer_mode = QCheckBox(
            "Developer mode (permits otherwise-blocked categories, still confirmed)"
        )
        self.developer_mode.setChecked(settings.developer_mode)
        layout.addWidget(self.developer_mode)

        # --- Buttons --------------------------------------------------------
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Save")
        save.setObjectName("SendButton")
        save.clicked.connect(self.accept)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def updated_settings(self) -> Settings:
        """Return a Settings object reflecting the dialog's current values."""
        return self._settings.model_copy(
            update={
                "llm_provider": self.provider_box.currentText(),
                "llm_model": self.model_edit.text().strip(),
                "openai_api_key": self.openai_key.text().strip() or None,
                "anthropic_api_key": self.anthropic_key.text().strip() or None,
                "ollama_base_url": self.ollama_url.text().strip() or "http://localhost:11434",
                "agent_mode": AgentMode(self.mode_box.currentText()),
                "voice_enabled": self.voice_enabled.isChecked(),
                "stt_provider": self.stt_box.currentText(),
                "tts_provider": self.tts_box.currentText(),
                "voice_speed": float(self.voice_speed.value()),
                "voice_autosend": self.voice_autosend.isChecked(),
                "screen_access_enabled": self.screen_toggle.isChecked(),
                "automation_enabled": self.automation_toggle.isChecked(),
                "screenshot_logging": self.screenshot_log.isChecked(),
                "developer_mode": self.developer_mode.isChecked(),
            }
        )
