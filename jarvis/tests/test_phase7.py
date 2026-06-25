"""Tests for Phase 7: global hotkey, tray-related settings, and wake word stub."""
from __future__ import annotations


def test_global_hotkey_available_and_start_are_graceful():
    from jarvis.ui.global_hotkey import GlobalHotkey

    hk = GlobalHotkey("ctrl+shift+j")
    assert isinstance(hk.available(), bool)
    # 'keyboard' isn't installed in CI -> start() returns False, never raises.
    started = hk.start()
    assert isinstance(started, bool)
    hk.stop()  # safe even if not started


def test_phase7_settings_defaults():
    from jarvis.app.settings import Settings

    s = Settings()
    assert s.minimize_to_tray is True
    assert s.global_hotkey_enabled is True
    assert s.wake_word_enabled is False  # experimental, off by default


def test_phase7_settings_persist(tmp_path):
    from jarvis.app.config import EnvConfig
    from jarvis.app.settings import Settings
    from jarvis.storage.database import Database
    from jarvis.storage.secrets import SecretStore

    db = Database(tmp_path / "s.db")
    store = SecretStore(tmp_path / "secrets")
    s = Settings()
    s.minimize_to_tray = False
    s.global_hotkey_enabled = False
    s.wake_word_enabled = True
    s.save(db, secrets=store)

    reloaded = Settings.load(db, EnvConfig(), secrets=store)
    assert reloaded.minimize_to_tray is False
    assert reloaded.global_hotkey_enabled is False
    assert reloaded.wake_word_enabled is True
    db.close()


def test_wake_word_remains_disabled_experimental():
    from jarvis.voice.wake_word import WakeWordDetector

    # Even when asked to enable, there is no always-on backend in this build.
    det = WakeWordDetector(enabled=True)
    assert det.is_available() is False
    assert det.start(lambda: None) is False
    assert det.running is False
