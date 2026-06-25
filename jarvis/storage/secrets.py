"""Encrypted storage for sensitive values (API keys, OAuth tokens).

Requirement: never store API keys or OAuth tokens in plaintext SQLite. Secrets
are therefore kept OUT of the settings table entirely and instead written to an
encrypted file (``~/.jarvis/secrets.enc``) using Fernet (AES-128-CBC + HMAC).
The Fernet key lives in ``~/.jarvis/secret.key`` with owner-only permissions.

If the ``cryptography`` package is unavailable, secrets are kept in memory for
the current session ONLY and never written to disk - we never fall back to
plaintext persistence.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Optional


def _default_dir() -> Path:
    return Path.home() / ".jarvis"


class SecretStore:
    def __init__(self, directory: Optional[Path] = None) -> None:
        self.dir = Path(directory) if directory is not None else _default_dir()
        self.enc_path = self.dir / "secrets.enc"
        self.key_path = self.dir / "secret.key"
        self._cache: dict[str, str] = {}
        self._fernet = None
        self._init_backend()
        self._load()

    # -- backend -------------------------------------------------------------
    def _init_backend(self) -> None:
        # Note: catch BaseException because a broken/native crypto backend can
        # raise non-Exception errors (e.g. a Rust panic via pyo3). In every such
        # case we degrade to memory-only and NEVER fall back to plaintext.
        try:
            from cryptography.fernet import Fernet
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:  # noqa: BLE001 - missing/broken dependency
            self._fernet = None
            return
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            if self.key_path.exists():
                key = self.key_path.read_bytes()
            else:
                key = Fernet.generate_key()
                self.key_path.write_bytes(key)
                _restrict(self.key_path)
            fernet = Fernet(key)
            # Functional probe: confirm the backend actually encrypts/decrypts.
            if fernet.decrypt(fernet.encrypt(b"probe")) != b"probe":
                raise RuntimeError("crypto self-test failed")
            self._fernet = fernet
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:  # noqa: BLE001 - never let this break startup
            self._fernet = None

    @property
    def persistent(self) -> bool:
        """True if secrets are encrypted-at-rest; False = memory-only session."""
        return self._fernet is not None

    # -- load/persist --------------------------------------------------------
    def _load(self) -> None:
        if self._fernet is None or not self.enc_path.exists():
            return
        try:
            token = self.enc_path.read_bytes()
            data = self._fernet.decrypt(token)
            self._cache = json.loads(data.decode("utf-8"))
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:  # noqa: BLE001 - corrupt/foreign file -> start empty
            self._cache = {}

    def _persist(self) -> None:
        if self._fernet is None:
            return  # memory-only; never write plaintext
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            token = self._fernet.encrypt(json.dumps(self._cache).encode("utf-8"))
            self.enc_path.write_bytes(token)
            _restrict(self.enc_path)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:  # noqa: BLE001
            pass

    # -- API -----------------------------------------------------------------
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = self._cache.get(key)
        return value if value is not None else default

    def set(self, key: str, value: Optional[str]) -> None:
        if value is None or value == "":
            self.delete(key)
            return
        self._cache[key] = value
        self._persist()

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            self._persist()

    def keys(self) -> list[str]:
        return list(self._cache.keys())


def _restrict(path: Path) -> None:
    """Best-effort: make a file readable/writable by the owner only."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass


# Process-wide default store (lazily created).
_DEFAULT_STORE: Optional[SecretStore] = None


def get_secret_store() -> SecretStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = SecretStore()
    return _DEFAULT_STORE
