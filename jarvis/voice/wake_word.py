"""Offline wake-word engine (experimental, disabled by default).

Listens locally for the wake phrase "Hey Jarvis" using openWakeWord. Audio is
processed entirely on-device and is NEVER streamed to OpenAI or any cloud
service. There is no stealth listening: the UI shows a clear "wake listening"
indicator whenever this is running, and it only runs while JARVIS is alive (in
the tray/foreground) and the user has both voice AND wake word enabled.

If the optional dependencies are missing, ``start()`` returns a clear setup
message naming the exact interpreter. Importing this module never fails.
"""
from __future__ import annotations

import sys
import threading
import time
from typing import Callable, Optional, Tuple


def _deps_available() -> bool:
    try:
        import numpy  # noqa: F401
        import openwakeword  # noqa: F401
        import sounddevice  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def setup_message() -> str:
    exe = sys.executable
    return (
        "Wake word needs an offline engine, which isn't installed in the "
        "interpreter running JARVIS.\n"
        f"Running interpreter: {sys.executable}\n"
        "Install it into THIS interpreter:\n"
        f'    "{exe}" -m pip install openwakeword sounddevice numpy\n'
        "Detection runs fully on-device - microphone audio is never sent to the "
        "cloud."
    )


class WakeWordEngine:
    """Background offline wake-word listener for 'Hey Jarvis'."""

    def __init__(self, phrase: str = "Hey Jarvis", threshold: float = 0.5) -> None:
        self.phrase = phrase
        self.threshold = threshold
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._running = False

    def available(self) -> bool:
        return _deps_available()

    def setup_message(self) -> str:
        return setup_message()

    @property
    def running(self) -> bool:
        return self._running

    def _model_key(self) -> str:
        # openWakeWord ships a pretrained "hey_jarvis" model.
        return "hey_jarvis"

    def start(self, on_detected: Callable[[], None]) -> Tuple[bool, str]:
        """Start listening. Returns (ok, error_message). Non-blocking."""
        if self._running:
            return True, ""
        if not self.available():
            return False, self.setup_message()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, args=(on_detected,), name="jarvis-wake", daemon=True
        )
        self._thread.start()
        self._running = True
        return True, ""

    def _run(self, on_detected: Callable[[], None]) -> None:
        try:
            import numpy as np  # noqa: F401
            import sounddevice as sd
            from openwakeword.model import Model
        except Exception:  # noqa: BLE001
            self._running = False
            return

        try:
            try:
                model = Model(wakeword_models=[self._model_key()])
            except Exception:  # noqa: BLE001 - fall back to all pretrained models
                model = Model()
        except Exception:  # noqa: BLE001 - models not downloaded etc.
            self._running = False
            return

        try:
            with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280) as stream:
                last_fire = 0.0
                while not self._stop.is_set():
                    data, _ = stream.read(1280)
                    try:
                        scores = model.predict(data.flatten())
                    except Exception:  # noqa: BLE001
                        continue
                    if any(score >= self.threshold for score in scores.values()):
                        now = time.time()
                        if now - last_fire > 2.0:  # debounce repeated triggers
                            last_fire = now
                            try:
                                on_detected()
                            except Exception:  # noqa: BLE001
                                pass
        except Exception:  # noqa: BLE001 - mic/device errors must not crash
            pass
        finally:
            self._running = False

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._running = False


# Backwards-compatible alias for earlier code/tests.
WakeWordDetector = WakeWordEngine
