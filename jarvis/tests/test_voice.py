"""Tests for the Phase 3 voice subsystem (STT / TTS / recorder).

These are Qt-free: they exercise the voice backends directly, so they run on any
platform with or without the optional audio packages installed.
"""
from __future__ import annotations

import threading


def test_voice_modules_import_without_crashing():
    # Importing must never fail regardless of platform / optional deps.
    import jarvis.voice.recorder  # noqa: F401
    import jarvis.voice.stt  # noqa: F401
    import jarvis.voice.tts  # noqa: F401
    import jarvis.voice.wake_word  # noqa: F401


# --------------------------------------------------------------------------- #
# STT
# --------------------------------------------------------------------------- #
def test_disabled_stt_returns_graceful_message():
    from jarvis.voice.stt import DisabledSTT

    stt = DisabledSTT()
    assert stt.is_available() is False
    result = stt.transcribe("nonexistent.wav")
    assert result.ok is False
    assert result.text == ""
    assert result.error  # a non-empty, human-readable message


def test_openai_stt_without_key_is_unavailable_with_clear_setup_message():
    from jarvis.voice.stt import OpenAIWhisperSTT

    stt = OpenAIWhisperSTT(api_key=None)
    assert stt.is_available() is False
    msg = stt.availability_message()
    assert "OPENAI_API_KEY" in msg
    # transcribe must also fail gracefully, never raise.
    result = stt.transcribe("whatever.wav")
    assert result.ok is False
    assert "OPENAI_API_KEY" in result.error


def test_get_stt_provider_selects_openai_when_requested():
    from jarvis.voice.stt import OpenAIWhisperSTT, get_stt_provider

    stt = get_stt_provider("openai-whisper", api_key="sk-test")
    assert isinstance(stt, OpenAIWhisperSTT)


def test_get_stt_provider_defaults_to_disabled():
    from jarvis.voice.stt import DisabledSTT, get_stt_provider

    assert isinstance(get_stt_provider("disabled"), DisabledSTT)
    assert isinstance(get_stt_provider("anything-unknown"), DisabledSTT)


# --------------------------------------------------------------------------- #
# TTS
# --------------------------------------------------------------------------- #
def test_disabled_tts_is_a_safe_noop_with_message():
    from jarvis.voice.tts import DisabledTTS

    tts = DisabledTTS()
    assert tts.is_available() is False
    assert tts.speak("hello") is False
    assert tts.availability_message()  # clear setup instructions


def test_get_tts_provider_falls_back_when_backend_missing():
    from jarvis.voice.tts import DisabledTTS, Pyttsx3TTS, get_tts_provider

    tts = get_tts_provider("pyttsx3")
    # Either pyttsx3 is installed (real engine) or we get the safe no-op.
    assert isinstance(tts, (Pyttsx3TTS, DisabledTTS))
    if isinstance(tts, DisabledTTS):
        assert tts.speak("hi") is False


def test_get_tts_provider_disabled_explicit():
    from jarvis.voice.tts import DisabledTTS, get_tts_provider

    assert isinstance(get_tts_provider("disabled"), DisabledTTS)


# --------------------------------------------------------------------------- #
# Recorder
# --------------------------------------------------------------------------- #
def test_recorder_is_available_never_raises():
    from jarvis.voice.recorder import AudioRecorder

    assert isinstance(AudioRecorder().is_available(), bool)


def test_recorder_without_backend_returns_clear_setup_message():
    from jarvis.voice.recorder import AudioRecorder

    rec = AudioRecorder()
    if rec.is_available():
        return  # backend present in this env; nothing to assert here.
    path, err = rec.record(threading.Event())
    assert path is None
    assert err is not None
    assert "sounddevice" in err or "Microphone" in err


# --------------------------------------------------------------------------- #
# Settings defaults
# --------------------------------------------------------------------------- #
def test_voice_disabled_by_default():
    from jarvis.app.settings import Settings

    s = Settings()
    assert s.voice_enabled is False
    assert s.voice_autosend is False
    assert s.stt_provider == "openai-whisper"
    assert s.tts_provider == "pyttsx3"


def test_new_status_values_exist():
    from jarvis.storage.models import AgentStatus

    assert AgentStatus.TRANSCRIBING.value == "Transcribing"
    assert AgentStatus.SPEAKING.value == "Speaking"
