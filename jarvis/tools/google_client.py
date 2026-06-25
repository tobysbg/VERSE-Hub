"""Google (Gmail + Calendar) OAuth/API client (Phase 6).

Uses the official Google API client libraries - NOT screen-clicking. The OAuth
token is stored ONLY in the encrypted SecretStore (never plaintext SQLite). All
imports are lazy and every failure is reported as a clear message, so missing
libraries or credentials can never crash the rest of JARVIS.

Setup (one-time, by the user):
  1. Create a Google Cloud project, enable the Gmail API and Calendar API.
  2. Create an OAuth client (Desktop app) and download ``credentials.json``.
  3. Place ``credentials.json`` in ``~/.jarvis/`` (or the working directory).
  4. The first Gmail/Calendar action opens a browser to authorize; the token is
     then saved encrypted for next time.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from ..storage.secrets import SecretStore, get_secret_store

# Read + compose/send mail, and full calendar (create/delete need write scope).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

_TOKEN_SECRET_KEY = "google_token"


def google_libs_available() -> bool:
    try:
        import google.oauth2.credentials  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def credentials_path() -> Optional[Path]:
    """Locate the user's OAuth client credentials.json, if present."""
    for candidate in (Path.home() / ".jarvis" / "credentials.json", Path.cwd() / "credentials.json"):
        if candidate.exists():
            return candidate
    return None


SETUP_HINT = (
    "Google is not set up. To enable Gmail/Calendar:\n"
    "  1. Install libs: pip install google-api-python-client google-auth-oauthlib\n"
    "  2. Enable the Gmail + Calendar APIs in a Google Cloud project.\n"
    "  3. Create an OAuth 'Desktop app' client and download credentials.json.\n"
    "  4. Put credentials.json in ~/.jarvis/ (the first action opens a browser "
    "to authorize). The token is stored encrypted, never in plaintext."
)


class GoogleClient:
    def __init__(self, secrets: Optional[SecretStore] = None) -> None:
        self.secrets = secrets or get_secret_store()

    # -- availability --------------------------------------------------------
    def setup_message(self) -> str:
        if not google_libs_available():
            return SETUP_HINT
        if credentials_path() is None:
            return (
                "Google API libraries are installed, but no credentials.json was "
                "found in ~/.jarvis/ or the current directory.\n" + SETUP_HINT
            )
        return "ready"

    def available(self) -> bool:
        return google_libs_available() and credentials_path() is not None

    # -- auth ----------------------------------------------------------------
    def get_credentials(self) -> Tuple[Optional[Any], str]:
        """Return (credentials, '') or (None, error_message). May open a browser."""
        if not google_libs_available():
            return None, SETUP_HINT
        creds_file = credentials_path()
        if creds_file is None:
            return None, self.setup_message()

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        token_json = self.secrets.get(_TOKEN_SECRET_KEY)
        if token_json:
            try:
                import json

                creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
            except Exception:  # noqa: BLE001
                creds = None

        try:
            if creds and creds.valid:
                return creds, ""
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_token(creds)
                return creds, ""
            # No valid token: run the interactive flow (opens a browser).
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
            self._save_token(creds)
            return creds, ""
        except Exception as exc:  # noqa: BLE001
            return None, f"Google authorization failed: {exc}"

    def _save_token(self, creds: Any) -> None:
        try:
            self.secrets.set(_TOKEN_SECRET_KEY, creds.to_json())
        except Exception:  # noqa: BLE001
            pass

    # -- services ------------------------------------------------------------
    def service(self, api: str, version: str) -> Tuple[Optional[Any], str]:
        creds, err = self.get_credentials()
        if creds is None:
            return None, err
        try:
            from googleapiclient.discovery import build

            return build(api, version, credentials=creds, cache_discovery=False), ""
        except Exception as exc:  # noqa: BLE001
            return None, f"Could not build the {api} service: {exc}"

    def gmail(self) -> Tuple[Optional[Any], str]:
        return self.service("gmail", "v1")

    def calendar(self) -> Tuple[Optional[Any], str]:
        return self.service("calendar", "v3")
