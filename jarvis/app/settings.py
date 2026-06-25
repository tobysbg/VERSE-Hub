"""Application settings: a pydantic model persisted in SQLite and overlaid by env.

Precedence (highest first):
    1. Values explicitly set in the in-app Settings dialog (stored in SQLite).
    2. Environment / .env values (API keys, default provider/model).
    3. Built-in safe defaults.

Critically: all capability toggles default to the SAFE position. Desktop
control and automation are OFF; developer "blocked" actions are OFF.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .config import EnvConfig
from ..storage.database import Database
from ..storage.models import AgentMode

# Settings keys we persist (kept in one place to avoid typos).
_SETTING_KEYS = [
    "llm_provider",
    "llm_model",
    "openai_api_key",
    "anthropic_api_key",
    "ollama_base_url",
    "agent_mode",
    "screen_access_enabled",
    "automation_enabled",
    "voice_enabled",
    "stt_provider",
    "tts_provider",
    "voice_speed",
    "developer_mode",
    "screenshot_logging",
]


class Settings(BaseModel):
    """Runtime settings object shared across the app."""

    # --- LLM -----------------------------------------------------------------
    llm_provider: str = "openai"
    llm_model: str = ""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"

    # --- Agent behaviour -----------------------------------------------------
    agent_mode: AgentMode = AgentMode.CONFIRMATION

    # --- Capability toggles (all default to the SAFE position) ---------------
    screen_access_enabled: bool = False
    automation_enabled: bool = False

    # --- Voice ---------------------------------------------------------------
    voice_enabled: bool = False
    stt_provider: str = "faster-whisper"
    tts_provider: str = "pyttsx3"
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)

    # --- Developer / advanced ------------------------------------------------
    # When True, "blocked" categories may be attempted (still confirmation-gated).
    developer_mode: bool = False
    # When True, raw screenshots may be written to disk for logging.
    screenshot_logging: bool = False

    # ------------------------------------------------------------------------
    @classmethod
    def load(cls, db: Database, env: EnvConfig) -> "Settings":
        """Build settings from env defaults, then overlay persisted values."""
        data: dict = {
            "llm_provider": env.llm_provider,
            "llm_model": env.llm_model,
            "openai_api_key": env.openai_api_key,
            "anthropic_api_key": env.anthropic_api_key,
            "ollama_base_url": env.ollama_base_url,
        }
        stored = db.all_settings()
        for key in _SETTING_KEYS:
            if key in stored and stored[key] is not None:
                data[key] = stored[key]
        # Drop Nones so pydantic defaults apply where appropriate.
        data = {k: v for k, v in data.items() if v is not None}
        return cls(**data)

    def save(self, db: Database) -> None:
        """Persist every known setting to the database."""
        dump = self.model_dump()
        for key in _SETTING_KEYS:
            value = dump.get(key)
            if isinstance(value, AgentMode):
                value = value.value
            db.set_setting(key, value)

    def active_api_key(self) -> Optional[str]:
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None  # ollama needs no key
