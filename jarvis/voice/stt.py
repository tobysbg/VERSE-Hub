"""Speech-to-text providers (Phase 3).

Two providers are wired:
  * ``OpenAIWhisperSTT`` - uses the OpenAI audio transcription API when an
    ``OPENAI_API_KEY`` is configured and the ``openai`` package is installed.
  * ``DisabledSTT`` - a safe no-op that returns a clear setup message.

Nothing here imports heavy/optional packages at module load, so importing this
module never crashes regardless of platform or what's installed.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class Transcription:
    text: str
    ok: bool = True
    error: str = ""


class STTProvider(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def is_available(self) -> bool:
        ...

    @abc.abstractmethod
    def availability_message(self) -> str:
        """Human-readable reason/instructions when not available (or 'ready')."""

    @abc.abstractmethod
    def transcribe(self, audio_path: str) -> Transcription:
        ...


class DisabledSTT(STTProvider):
    """Default STT: clearly reports that speech input is not enabled."""

    name = "disabled"

    def is_available(self) -> bool:
        return False

    def availability_message(self) -> str:
        return (
            "Speech-to-text is disabled. In Settings, set STT provider to "
            "'openai-whisper' and add your OPENAI_API_KEY to use voice input."
        )

    def transcribe(self, audio_path: str) -> Transcription:
        return Transcription(text="", ok=False, error=self.availability_message())


class OpenAIWhisperSTT(STTProvider):
    """Speech-to-text via the OpenAI audio transcription API."""

    name = "openai-whisper"

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1") -> None:
        self.api_key = api_key
        self.model = model

    def _openai_installed(self) -> bool:
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return bool(self.api_key) and self._openai_installed()

    def availability_message(self) -> str:
        if not self.api_key:
            return (
                "OpenAI speech-to-text needs an OPENAI_API_KEY. Add it in Settings "
                "(or your .env) and try again."
            )
        if not self._openai_installed():
            return "The 'openai' package is not installed. Run: pip install openai"
        return "ready"

    def transcribe(self, audio_path: str) -> Transcription:
        if not self.api_key:
            return Transcription(text="", ok=False, error=self.availability_message())
        try:
            from openai import OpenAI
        except ImportError:
            return Transcription(
                text="",
                ok=False,
                error="The 'openai' package is not installed. Run: pip install openai",
            )
        try:
            client = OpenAI(api_key=self.api_key)
            with open(audio_path, "rb") as fh:
                resp = client.audio.transcriptions.create(model=self.model, file=fh)
            text = getattr(resp, "text", "") or ""
        except FileNotFoundError:
            return Transcription(text="", ok=False, error="No recorded audio was found.")
        except Exception as exc:  # noqa: BLE001 - surface as graceful error
            return Transcription(text="", ok=False, error=f"Transcription failed: {exc}")
        return Transcription(text=text, ok=True)


def get_stt_provider(name: str = "disabled", api_key: Optional[str] = None) -> STTProvider:
    """Select an STT provider by name. Falls back to a safe no-op."""
    if name == "openai-whisper":
        return OpenAIWhisperSTT(api_key=api_key)
    return DisabledSTT()
