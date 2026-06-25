"""Optional 'Start JARVIS with Windows' helper (OFF by default).

Implemented via a small launcher script in the user's Windows Startup folder, so
it is transparent and trivially reversible (no registry hacks, no elevation).
Never enabled automatically - only when the user ticks the setting.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple


def _repo_root() -> Path:
    # jarvis/app/autostart.py -> repo root (parent of the 'jarvis' package).
    return Path(__file__).resolve().parent.parent.parent


def _startup_dir() -> Optional[Path]:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _entry_path() -> Optional[Path]:
    d = _startup_dir()
    return (d / "JARVIS.bat") if d else None


def is_supported() -> bool:
    return sys.platform == "win32"


def is_enabled() -> bool:
    p = _entry_path()
    return bool(p and p.exists())


def set_enabled(enabled: bool) -> Tuple[bool, str]:
    """Enable/disable launching JARVIS at Windows login. Returns (ok, message)."""
    if not is_supported():
        return False, "'Start with Windows' is only supported on Windows."
    path = _entry_path()
    if path is None:
        return False, "Could not locate the Windows Startup folder (no %APPDATA%)."
    try:
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                "@echo off\r\n"
                f'cd /d "{_repo_root()}"\r\n'
                f'start "" "{sys.executable}" -m jarvis.app.main\r\n'
            )
            path.write_text(content, encoding="utf-8")
            return True, f"JARVIS will start with Windows ({path})."
        if path.exists():
            path.unlink()
        return True, "JARVIS will no longer start with Windows."
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not update the startup entry: {exc}"
