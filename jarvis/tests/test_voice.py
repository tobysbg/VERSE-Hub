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


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #
def test_probe_module_reports_success_and_failure():
    from jarvis.voice.diagnostics import probe_module

    ok, err = probe_module("sys")  # always importable
    assert ok is True and err == ""

    ok, err = probe_module("a_module_that_does_not_exist_zzz")
    assert ok is False
    assert "ModuleNotFoundError" in err or "ImportError" in err


def test_audio_backend_status_shape():
    from jarvis.voice.diagnostics import audio_backend_status

    ok, errors = audio_backend_status()
    assert isinstance(ok, bool)
    assert isinstance(errors, list)
    # When unavailable, there must be a concrete reason for each missing piece.
    if not ok:
        assert errors and all(isinstance(e, str) and e for e in errors)


def test_audio_backend_message_names_interpreter_when_unavailable():
    import sys

    from jarvis.voice.diagnostics import audio_backend_message, audio_backend_status

    ok, _ = audio_backend_status()
    msg = audio_backend_message()
    if ok:
        assert msg == "ready"
    else:
        # The whole point of the fix: tell the user WHICH interpreter is running.
        assert sys.executable in msg


def test_recorder_availability_message_matches_backend():
    import sys

    from jarvis.voice.recorder import AudioRecorder

    rec = AudioRecorder()
    msg = rec.availability_message()
    if rec.is_available():
        assert msg == "ready"
    else:
        assert sys.executable in msg


def test_voice_diagnostics_has_all_required_fields():
    from jarvis.app.settings import Settings
    from jarvis.voice.diagnostics import voice_diagnostics

    diag = voice_diagnostics(Settings())
    for key in (
        "executable",
        "numpy_installed",
        "sounddevice_installed",
        "stt_configured",
        "tts_configured",
    ):
        assert key in diag
    assert isinstance(diag["executable"], str) and diag["executable"]
    assert isinstance(diag["numpy_installed"], bool)
    assert isinstance(diag["sounddevice_installed"], bool)
    assert isinstance(diag["stt_configured"], bool)
    assert isinstance(diag["tts_configured"], bool)


def test_format_and_summary_render_without_error():
    from jarvis.app.settings import Settings
    from jarvis.voice.diagnostics import (
        format_diagnostics,
        summary_line,
        voice_diagnostics,
    )

    diag = voice_diagnostics(Settings())
    block = format_diagnostics(diag)
    assert "sys.executable" in block
    assert "numpy installed" in block
    line = summary_line(diag)
    assert "Voice diagnostics" in line


def test_recorder_is_available_consistent_with_backend_status():
    """If numpy+sounddevice import, is_available() MUST be True (the bug)."""
    from jarvis.voice.diagnostics import audio_backend_status
    from jarvis.voice.recorder import AudioRecorder

    ok, _ = audio_backend_status()
    assert AudioRecorder().is_available() is ok
