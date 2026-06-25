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
from ..storage.secrets import SecretStore, get_secret_store

# Non-sensitive settings persisted in the SQLite settings table.
_SETTING_KEYS = [
    "llm_provider",
    "llm_model",
    "ollama_base_url",
    "agent_mode",
    "screen_access_enabled",
    "automation_enabled",
    "voice_enabled",
    "stt_provider",
    "tts_provider",
    "tts_voice",
    "voice_speed",
    "voice_autosend",
    "read_responses_aloud",
    "developer_mode",
    "screenshot_logging",
]

# Sensitive values - NEVER stored in plaintext SQLite. Persisted only via the
# encrypted SecretStore (or kept in memory if encryption is unavailable).
_SECRET_KEYS = [
    "openai_api_key",
    "anthropic_api_key",
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

    # --- Voice (disabled by default; push-to-talk only, no wake word) --------
    voice_enabled: bool = False
    stt_provider: str = "openai-whisper"
    # TTS defaults to 'none' (pyttsx3 quality is poor); Settings.load() upgrades
    # this to 'edge-tts' on first run if that high-quality backend is installed.
    tts_provider: str = "none"
    tts_voice: str = ""  # provider-specific voice id; blank = provider default
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    # Auto-send a finished transcription (ON by default for a fast assistant
    # feel). When OFF, the transcript is placed in the input to review and send.
    voice_autosend: bool = True
    # Read assistant responses aloud. OFF by default (until a good TTS voice is
    # selected) so the poor offline voice isn't forced on the user.
    read_responses_aloud: bool = False

    # --- Developer / advanced ------------------------------------------------
    # When True, "blocked" categories may be attempted (still confirmation-gated).
    developer_mode: bool = False
    # When True, raw screenshots may be written to disk for logging.
    screenshot_logging: bool = False

    # ------------------------------------------------------------------------
    @classmethod
    def load(
        cls,
        db: Database,
        env: EnvConfig,
        secrets: Optional[SecretStore] = None,
    ) -> "Settings":
        """Build settings from env defaults, then overlay persisted values.

        API keys come from the env first, then from the encrypted SecretStore
        (which takes precedence, mirroring how UI-set values override .env). They
        are never read from or written to the SQLite settings table.
        """
        secrets = secrets or get_secret_store()
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
        # Overlay secrets from the encrypted store (precedence over env).
        for key in _SECRET_KEYS:
            secret_value = secrets.get(key)
            if secret_value:
                data[key] = secret_value
        # Drop Nones so pydantic defaults apply where appropriate.
        data = {k: v for k, v in data.items() if v is not None}

        # First run only (no persisted TTS choice): pick the best available
        # high-quality TTS - edge-tts if installed, otherwise 'none'.
        if "tts_provider" not in stored:
            try:
                from ..voice.tts import recommended_default_tts

                data["tts_provider"] = recommended_default_tts()
            except Exception:  # noqa: BLE001 - never let this break startup
                pass

        return cls(**data)

    def save(self, db: Database, secrets: Optional[SecretStore] = None) -> None:
        """Persist non-secret settings to SQLite and secrets to the SecretStore."""
        secrets = secrets or get_secret_store()
        dump = self.model_dump()
        for key in _SETTING_KEYS:
            value = dump.get(key)
            if isinstance(value, AgentMode):
                value = value.value
            db.set_setting(key, value)
        # Sensitive values go ONLY to the encrypted store (never plaintext SQLite).
        for key in _SECRET_KEYS:
            secrets.set(key, dump.get(key))

    def active_api_key(self) -> Optional[str]:
        if self.llm_provider == "openai":
            return self.openai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None  # ollama needs no key
