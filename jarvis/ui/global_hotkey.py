"""Optional OS-wide global hotkey to summon JARVIS (Phase 7).

A truly global hotkey (working even when the window is unfocused/minimized)
needs an OS-level listener. We use the optional ``keyboard`` package if it's
installed; otherwise we degrade gracefully and the app falls back to the in-app
``Ctrl+Shift+J`` shortcut (which only works when the window has focus).

The ``keyboard`` package may require elevated privileges on some systems and is
Windows/Linux-friendly. It is intentionally optional.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class GlobalHotkey(QObject):
    activated = Signal()

    def __init__(self, combo: str = "ctrl+shift+j") -> None:
        super().__init__()
        self.combo = combo
        self._handle = None

    def available(self) -> bool:
        try:
            import keyboard  # noqa: F401
            return True
        except Exception:  # noqa: BLE001 - import can fail w/o permissions
            return False

    def start(self) -> bool:
        """Register the hotkey. Returns True if a global hotkey is now active."""
        if not self.available():
            return False
        try:
            import keyboard

            # The callback fires on keyboard's listener thread; emitting a Qt
            # signal from there is delivered safely to the GUI thread (queued).
            self._handle = keyboard.add_hotkey(self.combo, lambda: self.activated.emit())
            return True
        except Exception:  # noqa: BLE001
            self._handle = None
            return False

    def stop(self) -> None:
        if self._handle is None:
            return
        try:
            import keyboard

            keyboard.remove_hotkey(self._handle)
        except Exception:  # noqa: BLE001
            pass
        self._handle = None
