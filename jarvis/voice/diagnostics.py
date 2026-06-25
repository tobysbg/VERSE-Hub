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


def voice_diagnostics(settings: Optional[object] = None) -> dict:
    """Collect a snapshot of the voice environment for logging/display."""
    np_ok, np_err = probe_module("numpy")
    sd_ok, sd_err = probe_module("sounddevice")

    stt_ok = False
    tts_ok = False
    if settings is not None:
        # Imported lazily to avoid a hard dependency cycle.
        from .stt import get_stt_provider
        from .tts import get_tts_provider

        stt_provider = getattr(settings, "stt_provider", "disabled")
        api_key = getattr(settings, "openai_api_key", None)
        tts_provider = getattr(settings, "tts_provider", "disabled")
        stt_ok = get_stt_provider(stt_provider, api_key).is_available()
        tts_ok = get_tts_provider(tts_provider).is_available()

    return {
        "executable": sys.executable,
        "python_version": sys.version.split()[0],
        "numpy_installed": np_ok,
        "numpy_error": np_err,
        "sounddevice_installed": sd_ok,
        "sounddevice_error": sd_err,
        "stt_configured": stt_ok,
        "tts_configured": tts_ok,
    }


def format_diagnostics(diag: dict) -> str:
    """Render a diagnostics dict as a readable multi-line block."""
    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    lines = [
        f"sys.executable      : {diag['executable']}",
        f"Python version      : {diag['python_version']}",
        f"numpy installed     : {yn(diag['numpy_installed'])}"
        + (f"  [{diag['numpy_error']}]" if diag.get("numpy_error") else ""),
        f"sounddevice installed: {yn(diag['sounddevice_installed'])}"
        + (f"  [{diag['sounddevice_error']}]" if diag.get("sounddevice_error") else ""),
        f"STT provider ready  : {yn(diag['stt_configured'])}",
        f"TTS provider ready  : {yn(diag['tts_configured'])}",
    ]
    return "\n".join(lines)


def summary_line(diag: dict) -> str:
    """A compact one-line summary for the action timeline."""
    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    return (
        f"Voice diagnostics — numpy:{yn(diag['numpy_installed'])} "
        f"sounddevice:{yn(diag['sounddevice_installed'])} "
        f"STT:{yn(diag['stt_configured'])} TTS:{yn(diag['tts_configured'])} "
        f"| {diag['executable']}"
    )
