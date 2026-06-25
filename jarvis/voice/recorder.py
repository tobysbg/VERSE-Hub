"""Microphone capture for push-to-talk voice input (Phase 3).

Recording is **explicit and bounded**: it only happens when the UI calls
``record()`` (i.e. the user pressed the mic button), it stops as soon as the
provided stop event is set, and it never runs longer than ``max_seconds``.
There is no always-on listening and no wake word.

The audio backend (``sounddevice`` + ``numpy``) is imported lazily, so importing
this module never fails. If the backend is missing, ``record()`` returns a clear
setup message instead of raising.
"""
from __future__ import annotations

import tempfile
import threading
import time
import wave
from typing import Callable, Optional, Tuple

_SETUP_HINT = (
    "Microphone capture needs the audio backend. Run: "
    "pip install sounddevice numpy"
)


class AudioRecorder:
    def __init__(
        self,
        samplerate: int = 16000,
        channels: int = 1,
        max_seconds: int = 60,
        block_frames: int = 1024,
    ) -> None:
        self.samplerate = samplerate
        self.channels = channels
        self.max_seconds = max_seconds
        self.block_frames = block_frames

    def is_available(self) -> bool:
        """True if the optional audio backend is importable. Never raises."""
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
            return True
        except Exception:  # noqa: BLE001 - missing system libs can raise OSError too
            return False

    def record(
        self,
        stop_event: threading.Event,
        on_level: Optional[Callable[[float], None]] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Record until ``stop_event`` is set (or ``max_seconds`` elapses).

        Returns ``(wav_path, None)`` on success or ``(None, error_message)``.
        Blocks - call this from a worker thread.
        """
        try:
            import numpy as np
            import sounddevice as sd
        except Exception:  # noqa: BLE001
            return None, _SETUP_HINT

        frames: list = []
        try:
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="int16",
            ) as stream:
                start = time.time()
                while not stop_event.is_set() and (time.time() - start) < self.max_seconds:
                    data, _overflow = stream.read(self.block_frames)
                    frames.append(data.copy())
                    if on_level is not None:
                        # Cheap RMS level for an optional waveform meter.
                        try:
                            on_level(float(np.abs(data).mean()) / 32768.0)
                        except Exception:  # noqa: BLE001
                            pass
        except Exception as exc:  # noqa: BLE001
            return None, (
                f"Could not access the microphone ({exc}). Check that an input "
                f"device is connected and that JARVIS has microphone permission."
            )

        if not frames:
            return None, "No audio was captured."

        audio = np.concatenate(frames, axis=0)
        try:
            tmp = tempfile.NamedTemporaryFile(prefix="jarvis_rec_", suffix=".wav", delete=False)
            tmp.close()
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # int16 = 2 bytes
                wf.setframerate(self.samplerate)
                wf.writeframes(audio.tobytes())
        except Exception as exc:  # noqa: BLE001
            return None, f"Could not save the recording: {exc}"

        return tmp.name, None
