"""Voice/audio environment diagnostics.

The #1 cause of "audio backend missing" reports is JARVIS running under a
*different* Python interpreter than the virtualenv where the user installed
``sounddevice``/``numpy`` (or ``import sounddevice`` raising a non-ImportError,
e.g. a PortAudio load error, only inside the GUI process). These helpers probe
imports **in the current process** and report ``sys.executable`` plus the actual
exception so the mismatch is obvious instead of hidden behind a generic message.
"""
from __future__ import annotations

import importlib
import sys
from typing import Optional


def probe_module(name: str) -> tuple[bool, str]:
    """Try to import ``name`` in THIS interpreter. Returns (ok, error_detail)."""
    try:
        importlib.import_module(name)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - capture ImportError, OSError, etc.
        return False, f"{type(exc).__name__}: {exc}"


def audio_backend_status() -> tuple[bool, list[str]]:
    """Check the microphone-capture backend (numpy + sounddevice).

    Returns ``(ok, errors)`` where ``errors`` lists the specific failures.
    """
    np_ok, np_err = probe_module("numpy")
    sd_ok, sd_err = probe_module("sounddevice")
    errors: list[str] = []
    if not np_ok:
        errors.append(f"numpy -> {np_err}")
    if not sd_ok:
        errors.append(f"sounddevice -> {sd_err}")
    return (np_ok and sd_ok), errors


def audio_backend_message() -> str:
    """A detailed, actionable message naming the interpreter and real errors."""
    ok, errors = audio_backend_status()
    if ok:
        return "ready"
    detail = "\n".join(f"  - {e}" for e in errors)
    return (
        "Microphone capture backend is not usable in the interpreter running "
        "JARVIS.\n"
        f"Running interpreter: {sys.executable}\n"
        f"{detail}\n"
        "Install the backend into THIS interpreter (note the path above):\n"
        f'  "{sys.executable}" -m pip install sounddevice numpy'
    )


def microphone_available() -> bool:
    """Best-effort: is at least one audio INPUT device present? Never raises."""
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        return any(int(d.get("max_input_channels", 0)) > 0 for d in devices)
    except Exception:  # noqa: BLE001
        return False


def stt_backend_installed(stt_provider: str) -> bool:
    """Is the import backend for the selected STT provider present?"""
    if stt_provider == "openai-whisper":
        return probe_module("openai")[0]
    return True  # 'disabled' needs nothing


def tts_backend_installed(tts_provider: str) -> bool:
    """Is the import backend for the selected TTS provider present?"""
    if tts_provider in ("none", "disabled", ""):
        return True
    if tts_provider == "pyttsx3":
        return probe_module("pyttsx3")[0]
    if tts_provider == "edge-tts":
        return probe_module("edge_tts")[0]
    if tts_provider == "openai-tts":
        return probe_module("openai")[0]
    return False


def voice_diagnostics(settings: Optional[object] = None) -> dict:
    """Collect a snapshot of the voice environment for logging/display."""
    np_ok, np_err = probe_module("numpy")
    sd_ok, sd_err = probe_module("sounddevice")

    stt_provider = getattr(settings, "stt_provider", "disabled") if settings else "disabled"
    tts_provider = getattr(settings, "tts_provider", "none") if settings else "none"
    api_key = getattr(settings, "openai_api_key", None) if settings else None
    selected_voice = getattr(settings, "tts_voice", "") if settings else ""

    stt_ready = False
    tts_ready = False
    if settings is not None:
        # Imported lazily to avoid a hard dependency cycle.
        from .stt import get_stt_provider
        from .tts import get_tts_provider

        stt_ready = get_stt_provider(stt_provider, api_key).is_available()
        tts_ready = get_tts_provider(tts_provider, api_key).is_available()

    return {
        "executable": sys.executable,
        "python_version": sys.version.split()[0],
        "numpy_installed": np_ok,
        "numpy_error": np_err,
        "sounddevice_installed": sd_ok,
        "sounddevice_error": sd_err,
        "microphone_detected": microphone_available(),
        "stt_provider": stt_provider,
        "stt_backend_installed": stt_backend_installed(stt_provider),
        "stt_configured": stt_ready,
        "tts_provider": tts_provider,
        "tts_backend_installed": tts_backend_installed(tts_provider),
        "tts_configured": tts_ready,
        "selected_voice": selected_voice or "(provider default)",
    }


def format_diagnostics(diag: dict) -> str:
    """Render a diagnostics dict as a readable multi-line block."""
    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    lines = [
        f"sys.executable        : {diag['executable']}",
        f"Python version        : {diag['python_version']}",
        f"numpy installed       : {yn(diag['numpy_installed'])}"
        + (f"  [{diag['numpy_error']}]" if diag.get("numpy_error") else ""),
        f"sounddevice installed : {yn(diag['sounddevice_installed'])}"
        + (f"  [{diag['sounddevice_error']}]" if diag.get("sounddevice_error") else ""),
        f"microphone detected   : {yn(diag.get('microphone_detected', False))}",
        f"STT backend installed : {yn(diag.get('stt_backend_installed', False))} "
        f"({diag.get('stt_provider', '?')})",
        f"STT provider ready    : {yn(diag['stt_configured'])}",
        f"TTS backend installed : {yn(diag.get('tts_backend_installed', False))} "
        f"({diag.get('tts_provider', '?')})",
        f"TTS provider ready    : {yn(diag['tts_configured'])}",
        f"selected voice        : {diag.get('selected_voice', '(provider default)')}",
    ]
    return "\n".join(lines)


def summary_line(diag: dict) -> str:
    """A compact one-line summary for the action timeline."""
    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    return (
        f"Voice diagnostics — mic:{yn(diag.get('microphone_detected', False))} "
        f"STT:{yn(diag['stt_configured'])} TTS:{yn(diag['tts_configured'])} "
        f"voice:{diag.get('selected_voice', '?')} | {diag['executable']}"
    )
