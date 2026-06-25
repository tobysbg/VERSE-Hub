"""Text-to-speech providers (Phase 3 polish).

Providers:
  * ``NoneTTS``     - explicit "no speech" option (never errors).
  * ``Pyttsx3TTS``  - offline, low quality; interruptible at sentence boundaries.
  * ``EdgeTTS``     - Microsoft Edge neural voices (high quality), needs the
                      ``edge-tts`` package; synthesizes then plays.
  * ``OpenAITTS``   - OpenAI TTS (high quality), needs ``openai`` + an API key.

All providers expose:
  * ``is_available()`` / ``availability_message()``
  * ``list_voices()`` -> list[(id, label)]
  * ``speak(text, speed, voice, should_stop)`` -> (ok, error)

``should_stop`` is an optional callable returning True when playback should be
interrupted (used by the Stop/Cancel button). Playback is performed in blocks so
it can be interrupted promptly and never blocks the UI thread (the caller runs
this on a worker thread).

Nothing imports heavy/optional packages at module load.
"""
from __future__ import annotations

import abc
import os
import re
import tempfile
from typing import Callable, List, Optional, Tuple

DEFAULT_EDGE_VOICE = "en-US-AriaNeural"
DEFAULT_OPENAI_VOICE = "alloy"

# A small curated set of good Edge neural voices. The full list is available via
# `edge-tts --list-voices`; users may also type any valid voice id in Settings.
_EDGE_VOICES = [
    ("en-US-AriaNeural", "English (US) - Aria"),
    ("en-US-GuyNeural", "English (US) - Guy"),
    ("en-US-JennyNeural", "English (US) - Jenny"),
    ("en-GB-SoniaNeural", "English (UK) - Sonia"),
    ("en-GB-RyanNeural", "English (UK) - Ryan"),
    ("en-AU-NatashaNeural", "English (AU) - Natasha"),
    ("de-DE-KatjaNeural", "German - Katja"),
    ("de-DE-ConradNeural", "German - Conrad"),
]
_OPENAI_VOICES = [
    (v, f"OpenAI - {v}") for v in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
]

ShouldStop = Optional[Callable[[], bool]]


class TTSProvider(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def is_available(self) -> bool:
        ...

    @abc.abstractmethod
    def availability_message(self) -> str:
        ...

    def list_voices(self) -> List[Tuple[str, str]]:
        return []

    @abc.abstractmethod
    def speak(
        self,
        text: str,
        speed: float = 1.0,
        voice: str = "",
        should_stop: ShouldStop = None,
    ) -> Tuple[bool, str]:
        """Speak ``text``. Returns ``(ok, error_message)``. Must not raise."""


# --------------------------------------------------------------------------- #
# None / disabled
# --------------------------------------------------------------------------- #
class NoneTTS(TTSProvider):
    """Explicit 'do not speak' provider. Always available, never speaks/errors."""

    name = "none"

    def is_available(self) -> bool:
        return True

    def availability_message(self) -> str:
        return "ready"

    def speak(self, text, speed=1.0, voice="", should_stop=None) -> Tuple[bool, str]:
        return True, ""  # graceful no-op


# Backwards-compatible alias (older code/tests referenced DisabledTTS).
class DisabledTTS(NoneTTS):
    name = "disabled"

    def availability_message(self) -> str:
        return (
            "Text-to-speech is off. Choose a TTS provider in Settings "
            "(edge-tts recommended for quality)."
        )


# --------------------------------------------------------------------------- #
# pyttsx3 (offline)
# --------------------------------------------------------------------------- #
class Pyttsx3TTS(TTSProvider):
    name = "pyttsx3"

    def is_available(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def availability_message(self) -> str:
        return "ready" if self.is_available() else (
            "The 'pyttsx3' package is not installed. Run: pip install pyttsx3"
        )

    def list_voices(self) -> List[Tuple[str, str]]:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices") or []
            return [(v.id, getattr(v, "name", v.id)) for v in voices]
        except Exception:  # noqa: BLE001
            return []

    def speak(self, text, speed=1.0, voice="", should_stop=None) -> Tuple[bool, str]:
        try:
            import pyttsx3
        except Exception:  # noqa: BLE001
            return False, "The 'pyttsx3' package is not installed. Run: pip install pyttsx3"
        try:
            engine = pyttsx3.init()
            base_rate = engine.getProperty("rate")
            engine.setProperty("rate", int(base_rate * speed))
            if voice:
                engine.setProperty("voice", voice)
            # Speak sentence-by-sentence so Stop can interrupt between sentences.
            for sentence in _split_sentences(text):
                if should_stop and should_stop():
                    break
                engine.say(sentence)
                engine.runAndWait()
            return True, ""
        except Exception as exc:  # noqa: BLE001
            return False, f"pyttsx3 failed: {exc}"


# --------------------------------------------------------------------------- #
# edge-tts (neural, online)
# --------------------------------------------------------------------------- #
class EdgeTTS(TTSProvider):
    name = "edge-tts"

    def is_available(self) -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def availability_message(self) -> str:
        if not self.is_available():
            return "The 'edge-tts' package is not installed. Run: pip install edge-tts"
        return "ready"

    def list_voices(self) -> List[Tuple[str, str]]:
        return list(_EDGE_VOICES)

    def speak(self, text, speed=1.0, voice="", should_stop=None) -> Tuple[bool, str]:
        try:
            import asyncio

            import edge_tts
        except Exception:  # noqa: BLE001
            return False, "The 'edge-tts' package is not installed. Run: pip install edge-tts"

        voice = voice or DEFAULT_EDGE_VOICE
        rate = _speed_to_rate(speed)
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis_tts_", suffix=".mp3", delete=False)
        tmp.close()
        try:
            async def _synth() -> None:
                comm = edge_tts.Communicate(text, voice, rate=rate)
                await comm.save(tmp.name)

            asyncio.run(_synth())
        except Exception as exc:  # noqa: BLE001
            _safe_remove(tmp.name)
            return False, f"edge-tts synthesis failed: {exc}"

        ok, err = _play_audio_file(tmp.name, should_stop)
        _safe_remove(tmp.name)
        return ok, err


# --------------------------------------------------------------------------- #
# OpenAI TTS (neural, online) - returns WAV so playback is dependency-light
# --------------------------------------------------------------------------- #
class OpenAITTS(TTSProvider):
    name = "openai-tts"

    def __init__(self, api_key: Optional[str] = None, model: str = "tts-1") -> None:
        self.api_key = api_key
        self.model = model

    def _openai_installed(self) -> bool:
        try:
            import openai  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def is_available(self) -> bool:
        return bool(self.api_key) and self._openai_installed()

    def availability_message(self) -> str:
        if not self.api_key:
            return "OpenAI TTS needs an OPENAI_API_KEY. Add it in Settings."
        if not self._openai_installed():
            return "The 'openai' package is not installed. Run: pip install openai"
        return "ready"

    def list_voices(self) -> List[Tuple[str, str]]:
        return list(_OPENAI_VOICES)

    def speak(self, text, speed=1.0, voice="", should_stop=None) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "OpenAI TTS needs an OPENAI_API_KEY. Add it in Settings."
        try:
            from openai import OpenAI
        except Exception:  # noqa: BLE001
            return False, "The 'openai' package is not installed. Run: pip install openai"

        voice = voice or DEFAULT_OPENAI_VOICE
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis_tts_", suffix=".wav", delete=False)
        tmp.close()
        try:
            client = OpenAI(api_key=self.api_key)
            resp = client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                response_format="wav",
                speed=max(0.25, min(4.0, speed)),
            )
            resp.stream_to_file(tmp.name)
        except Exception as exc:  # noqa: BLE001
            _safe_remove(tmp.name)
            return False, f"OpenAI TTS failed: {exc}"

        ok, err = _play_audio_file(tmp.name, should_stop)
        _safe_remove(tmp.name)
        return ok, err


# --------------------------------------------------------------------------- #
# Factory + helpers
# --------------------------------------------------------------------------- #
def get_tts_provider(
    name: str = "none",
    api_key: Optional[str] = None,
    voice: str = "",
) -> TTSProvider:
    if name == "pyttsx3":
        return Pyttsx3TTS()
    if name == "edge-tts":
        return EdgeTTS()
    if name == "openai-tts":
        return OpenAITTS(api_key=api_key)
    if name in ("disabled",):
        return DisabledTTS()
    return NoneTTS()


def recommended_default_tts() -> str:
    """Default TTS: edge-tts if available (high quality), otherwise 'none'."""
    if EdgeTTS().is_available():
        return "edge-tts"
    return "none"


def list_voices_for(name: str, api_key: Optional[str] = None) -> List[Tuple[str, str]]:
    return get_tts_provider(name, api_key=api_key).list_voices()


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p] or ([text] if text.strip() else [])


def _speed_to_rate(speed: float) -> str:
    """Map a 0.5..2.0 speed multiplier to edge-tts' '+N%' rate string."""
    pct = int(round((speed - 1.0) * 100))
    return f"{pct:+d}%"


def _safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def _read_audio(path: str):
    """Return (float32_samples, samplerate) or (None, error_message)."""
    try:
        import numpy as np
    except Exception as exc:  # noqa: BLE001
        return None, f"numpy is required for audio playback ({exc})."

    if path.lower().endswith(".wav"):
        try:
            import wave

            with wave.open(path, "rb") as wf:
                sr = wf.getframerate()
                ch = wf.getnchannels()
                raw = wf.readframes(wf.getnframes())
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if ch > 1:
                audio = audio.reshape(-1, ch)
            return audio, sr
        except Exception as exc:  # noqa: BLE001
            return None, f"Could not read WAV audio: {exc}"

    # Non-WAV (e.g. edge-tts mp3): needs soundfile (libsndfile).
    try:
        import soundfile as sf

        data, sr = sf.read(path, dtype="float32", always_2d=False)
        return data, sr
    except Exception as exc:  # noqa: BLE001
        return None, (
            "Could not decode the synthesized audio. Install 'soundfile' "
            "(pip install soundfile) for edge-tts playback, or use the "
            f"'openai-tts' / 'pyttsx3' provider. ({exc})"
        )


def _play_audio_file(path: str, should_stop: ShouldStop = None) -> Tuple[bool, str]:
    """Play an audio file in interruptible blocks. Returns (ok, error)."""
    try:
        import numpy as np
        import sounddevice as sd
    except Exception as exc:  # noqa: BLE001
        return False, (
            "Audio playback needs the audio backend. Run: pip install sounddevice "
            f"numpy ({exc})"
        )

    data, sr = _read_audio(path)
    if data is None:
        return False, sr  # sr holds the error message

    if getattr(data, "ndim", 1) == 1:
        channels = 1
    else:
        channels = data.shape[1]

    block = 2048
    try:
        with sd.OutputStream(samplerate=int(sr), channels=channels, dtype="float32") as stream:
            idx = 0
            total = len(data)
            while idx < total:
                if should_stop and should_stop():
                    break
                chunk = data[idx: idx + block]
                stream.write(np.ascontiguousarray(chunk, dtype="float32"))
                idx += block
    except Exception as exc:  # noqa: BLE001
        return False, f"Audio playback failed: {exc}"
    return True, ""
