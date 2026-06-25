"""Custom HUD widgets: animated radar, listening waveform, status indicator.

All artwork is procedural (drawn with QPainter) - there are no external image
assets, so nothing here can infringe any copyright. The visuals are an original
cyan/blue sci-fi console aesthetic.
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QLabel, QWidget

from ..storage.models import AgentStatus

_CYAN = QColor(95, 210, 255)
_DIM = QColor(40, 90, 120)


class RadarWidget(QWidget):
    """A rotating radar sweep with concentric rings - the HUD centrepiece."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self._angle = 0.0
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30 fps

    def set_active(self, active: bool) -> None:
        self._active = active

    def _tick(self) -> None:
        # Sweep faster when active, idle drift when not.
        self._angle = (self._angle + (6.0 if self._active else 1.2)) % 360.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt signature)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 6

        # Concentric rings.
        for i in range(1, 5):
            r = radius * i / 4
            pen = QPen(_DIM, 1)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Cross hairs.
        painter.setPen(QPen(QColor(40, 90, 120, 150), 1))
        painter.drawLine(int(cx - radius), int(cy), int(cx + radius), int(cy))
        painter.drawLine(int(cx), int(cy - radius), int(cx), int(cy + radius))

        # Sweep gradient.
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        grad = QRadialGradient(0, 0, radius)
        c0 = QColor(_CYAN)
        c0.setAlpha(160 if self._active else 70)
        grad.setColorAt(0.0, c0)
        grad.setColorAt(1.0, QColor(95, 210, 255, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawPie(int(-radius), int(-radius), int(radius * 2), int(radius * 2), 0, 40 * 16)
        painter.restore()

        # Centre dot.
        painter.setBrush(_CYAN)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 3, 3)
        painter.end()


class WaveformWidget(QWidget):
    """Animated audio waveform shown while listening/speaking."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(44)
        self._bars = [0.1] * 28
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)

    def set_active(self, active: bool) -> None:
        self._active = active
        if not active:
            self._bars = [0.08] * len(self._bars)
            self.update()

    def _tick(self) -> None:
        if not self._active:
            return
        self._bars = self._bars[1:] + [random.uniform(0.15, 1.0)]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        n = len(self._bars)
        bar_w = w / (n * 1.6)
        gap = bar_w * 0.6
        mid = h / 2
        color = QColor(_CYAN) if self._active else _DIM
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        for i, level in enumerate(self._bars):
            x = i * (bar_w + gap) + gap
            bar_h = max(3.0, level * (h - 8))
            painter.drawRoundedRect(
                int(x), int(mid - bar_h / 2), int(bar_w), int(bar_h), 2, 2
            )
        painter.end()


class StatusIndicator(QLabel):
    """A glowing pill that reflects the current agent status."""

    _COLORS = {
        AgentStatus.IDLE: "#4fb8e6",
        AgentStatus.LISTENING: "#43e0a0",
        AgentStatus.THINKING: "#ffcf5f",
        AgentStatus.ACTING: "#5fd2ff",
        AgentStatus.NEEDS_CONFIRMATION: "#ff9f43",
        AgentStatus.ERROR: "#ff5a6e",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_status(AgentStatus.IDLE)

    def set_status(self, status: AgentStatus) -> None:
        color = self._COLORS.get(status, "#4fb8e6")
        self.setText(f"  ●  {status.value.upper()}")
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 2px;
                border: 1px solid {color};
                border-radius: 12px;
                padding: 8px 14px;
                background-color: rgba(8, 18, 32, 0.85);
            }}
            """
        )


def pulse_phase(t: float) -> float:
    """Helper for any external pulse animation (0..1)."""
    return (math.sin(t) + 1) / 2
