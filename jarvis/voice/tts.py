"""Text-to-speech (Phase 3) - provider interface with safe default.

The default is a no-op that reports voice output is disabled. Real providers
(pyttsx3 offline, Edge TTS, or OpenAI TTS) implement ``speak``. ``pyttsx3`` is
used opportunistically if installed, since it is light and offline.
"""
from __future__ import annotations

import abc


class TTSProvider(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def is_available(self) -> bool:
        ...

    @abc.abstractmethod
    def speak(self, text: str, speed: float = 1.0) -> bool:
        """Speak text. Returns True if spoken, False if unavailable."""


class DisabledTTS(TTSProvider):
    name = "disabled"

    def is_available(self) -> bool:
        return False

    def speak(self, text: str, speed: float = 1.0) -> bool:
        return False


class Pyttsx3TTS(TTSProvider):
    """Offline TTS via pyttsx3, used only if the package is installed."""

    name = "pyttsx3"

    def is_available(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except ImportError:
            return False

    def speak(self, text: str, speed: float = 1.0) -> bool:
        try:
            import pyttsx3
        except ImportError:
            return False
        try:
            engine = pyttsx3.init()
            base_rate = engine.getProperty("rate")
            engine.setProperty("rate", int(base_rate * speed))
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception:  # noqa: BLE001 - never let TTS crash the app
            return False


def get_tts_provider(name: str = "disabled") -> TTSProvider:
    if name == "pyttsx3":
        provider = Pyttsx3TTS()
        if provider.is_available():
            return provider
    return DisabledTTS()
