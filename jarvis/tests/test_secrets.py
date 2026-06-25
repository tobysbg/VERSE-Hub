"""Tests for encrypted secret storage and that API keys never hit plaintext SQLite."""
from __future__ import annotations

import pytest

from jarvis.storage.secrets import SecretStore


def test_secret_roundtrip_in_session(tmp_path):
    # Works whether or not the crypto backend is functional (memory-only still
    # supports get/set within a session).
    store = SecretStore(tmp_path)
    store.set("openai_api_key", "sk-secret-123")
    assert store.get("openai_api_key") == "sk-secret-123"


def test_secret_persists_across_instances(tmp_path):
    store = SecretStore(tmp_path)
    if not store.persistent:
        pytest.skip("crypto backend not functional; secrets are memory-only here")
    store.set("anthropic_api_key", "sk-ant-xyz")
    reopened = SecretStore(tmp_path)
    assert reopened.get("anthropic_api_key") == "sk-ant-xyz"


def test_secret_file_is_encrypted_not_plaintext(tmp_path):
    store = SecretStore(tmp_path)
    if not store.persistent:
        pytest.skip("crypto backend not functional; nothing written to disk")
    store.set("openai_api_key", "sk-PLAINTEXT-MARKER")
    raw = (tmp_path / "secrets.enc").read_bytes()
    assert b"sk-PLAINTEXT-MARKER" not in raw  # value must be encrypted at rest


def test_no_plaintext_secret_file_when_backend_unavailable(tmp_path):
    store = SecretStore(tmp_path)
    store.set("openai_api_key", "sk-MEMORY-ONLY-MARKER")
    if store.persistent:
        pytest.skip("crypto backend functional; persistence covered elsewhere")
    # Memory-only mode must NEVER write a secrets file (no plaintext fallback).
    assert not (tmp_path / "secrets.enc").exists()


def test_secret_delete(tmp_path):
    store = SecretStore(tmp_path)
    store.set("openai_api_key", "x")
    store.set("openai_api_key", "")  # empty deletes
    assert store.get("openai_api_key") is None


def test_settings_do_not_store_api_keys_in_sqlite(tmp_path):
    from jarvis.app.config import EnvConfig
    from jarvis.app.settings import Settings
    from jarvis.storage.database import Database

    db = Database(tmp_path / "s.db")
    store = SecretStore(tmp_path / "secrets")
    s = Settings(openai_api_key="sk-should-be-secret", anthropic_api_key="sk-ant")
    s.save(db, secrets=store)

    # The SQLite settings table must NOT contain the API keys.
    all_settings = db.all_settings()
    assert "openai_api_key" not in all_settings
    assert "anthropic_api_key" not in all_settings
    # They must live in the encrypted store instead.
    assert store.get("openai_api_key") == "sk-should-be-secret"
    assert store.get("anthropic_api_key") == "sk-ant"
    db.close()


def test_settings_load_reads_api_key_from_secret_store(tmp_path):
    from jarvis.app.config import EnvConfig
    from jarvis.app.settings import Settings
    from jarvis.storage.database import Database

    db = Database(tmp_path / "s.db")
    store = SecretStore(tmp_path / "secrets")
    store.set("openai_api_key", "sk-from-store")

    loaded = Settings.load(db, EnvConfig(), secrets=store)
    assert loaded.openai_api_key == "sk-from-store"
    db.close()
