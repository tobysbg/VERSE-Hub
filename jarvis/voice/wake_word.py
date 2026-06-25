"""Wake-word detection (optional, Phase 3) - OFF by default.

This is intentionally a disabled stub. The MVP does NOT depend on a wake word;
a global hotkey is the primary trigger. A local wake-word engine (e.g.
openWakeWord) can be added later. The detector here never listens until both
``enabled`` is set AND a real backend is installed, and it can always be turned
off completely.
"""
from __future__ import annotations

from typing import Callable, Optional


class WakeWordDetector:
    def __init__(self, phrase: str = "hey jarvis", enabled: bool = False) -> None:
        self.phrase = phrase
        self.enabled = enabled
        self._running = False
        self._on_wake: Optional[Callable[[], None]] = None

    def is_available(self) -> bool:
        # No local backend wired up in this build.
        return False

    def start(self, on_wake: Callable[[], None]) -> bool:
        """Start listening. Returns False if disabled/unavailable (the default)."""
        if not self.enabled or not self.is_available():
            return False
        self._on_wake = on_wake
        self._running = True
        return True

    def stop(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running
