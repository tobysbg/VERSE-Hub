"""Environment configuration loading.

Reads the optional ``.env`` file (via python-dotenv) and exposes the values the
app needs. Nothing here ever raises on missing keys - callers must handle the
"not configured" case gracefully.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dotenv is a core dep, but stay defensive
    def load_dotenv(*_args, **_kwargs) -> bool:  # type: ignore
        return False


def _project_root() -> Path:
    # jarvis/app/config.py -> jarvis/
    return Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Load .env from the jarvis package dir or the current working directory."""
    candidates = [
        _project_root() / ".env",
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if path.exists():
            load_dotenv(path, override=False)
            return
    # Fall back to default search (no-op if nothing found).
    load_dotenv(override=False)


@dataclass
class EnvConfig:
    """Snapshot of environment-derived configuration."""

    llm_provider: str = "openai"
    llm_model: str = ""
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    @classmethod
    def from_environ(cls) -> "EnvConfig":
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openai").strip() or "openai",
            llm_model=os.getenv("LLM_MODEL", "").strip(),
            openai_api_key=_clean(os.getenv("OPENAI_API_KEY")),
            openai_base_url=_clean(os.getenv("OPENAI_BASE_URL")),
            anthropic_api_key=_clean(os.getenv("ANTHROPIC_API_KEY")),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
            or "http://localhost:11434",
        )


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def get_config() -> EnvConfig:
    """Load .env (once is fine; dotenv is idempotent) and return config."""
    load_env()
    return EnvConfig.from_environ()
