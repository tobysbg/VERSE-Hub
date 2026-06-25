"""Tests for the experimental offline wake-word engine and related settings."""
from __future__ import annotations

import sys


def test_wake_engine_import_and_availability_no_crash():
    from jarvis.voice.wake_word import WakeWordEngine

    eng = WakeWordEngine(phrase="Hey Jarvis")
    assert isinstance(eng.available(), bool)
    assert eng.running is False


def test_wake_setup_message_names_interpreter_and_commands():
    from jarvis.voice.wake_word import WakeWordEngine, setup_message

    msg = setup_message()
    assert sys.executable in msg
    assert "pip install openwakeword" in msg
    assert "sounddevice" in msg
    # The engine surfaces the same message.
    assert WakeWordEngine().setup_message() == msg


def test_wake_start_without_backend_is_graceful():
    from jarvis.voice.wake_word import WakeWordEngine

    eng = WakeWordEngine()
    if eng.available():
        return  # backend present in this env; nothing to assert here.
    ok, msg = eng.start(lambda: None)
    assert ok is False
    assert "openwakeword" in msg
    assert eng.running is False


def test_wake_settings_defaults():
    from jarvis.app.settings import Settings

    s = Settings()
    assert s.wake_word_enabled is False           # experimental, off by default
    assert s.wake_phrase == "Hey Jarvis"
    assert s.start_minimized is False
    assert s.start_with_windows is False


def test_wake_settings_persist(tmp_path):
    from jarvis.app.config import EnvConfig
    from jarvis.app.settings import Settings
    from jarvis.storage.database import Database
    from jarvis.storage.secrets import SecretStore

    db = Database(tmp_path / "s.db")
    store = SecretStore(tmp_path / "secrets")
    s = Settings()
    s.wake_word_enabled = True
    s.wake_phrase = "Hey Jarvis"
    s.start_minimized = True
    s.start_with_windows = True
    s.save(db, secrets=store)

    reloaded = Settings.load(db, EnvConfig(), secrets=store)
    assert reloaded.wake_word_enabled is True
    assert reloaded.start_minimized is True
    assert reloaded.start_with_windows is True
    db.close()


def test_autostart_helper_is_graceful_off_windows():
    from jarvis.app import autostart

    assert isinstance(autostart.is_supported(), bool)
    if not autostart.is_supported():
        ok, msg = autostart.set_enabled(True)
        assert ok is False
        assert "Windows" in msg
