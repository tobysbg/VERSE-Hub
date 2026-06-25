"""Speech-to-text (Phase 3) - provider interface with safe default.

The default implementation reports that voice is disabled. A real provider
(faster-whisper local, or the OpenAI Whisper API) can be dropped in by
implementing ``transcribe``. This keeps the MVP free of heavy ML dependencies
while leaving a clean seam.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


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
    def transcribe(self, audio_path: str) -> Transcription:
        ...


class DisabledSTT(STTProvider):
    """Default STT: clearly reports that speech input is not enabled."""

    name = "disabled"

    def is_available(self) -> bool:
        return False

    def transcribe(self, audio_path: str) -> Transcription:
        return Transcription(
            text="",
            ok=False,
            error=(
                "Speech-to-text is not enabled. Install faster-whisper "
                "(`pip install faster-whisper sounddevice`) and select it in "
                "Settings, or configure the OpenAI Whisper API."
            ),
        )


def get_stt_provider(name: str = "disabled") -> STTProvider:
    # Real providers are wired in a later phase; default stays safe.
    return DisabledSTT()
