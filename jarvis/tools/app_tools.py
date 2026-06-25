"""Application / window tools.

Windows-first: window enumeration and focus use ``pywinauto`` when available.
On other platforms (or when pywinauto is missing) the tools degrade gracefully
with a clear message, so the package imports and tests run anywhere.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, EmptyArgs, ToolResult

# Friendly aliases -> launch command, for common Windows apps.
_WINDOWS_APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "browser": "msedge.exe",
    "edge": "msedge.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
}


# --------------------------------------------------------------------------- #
# open_app
# --------------------------------------------------------------------------- #
class OpenAppArgs(BaseModel):
    app_name: str = Field(..., description="Name or executable of the app to open.")


class OpenAppTool(BaseTool):
    name = "open_app"
    description = "Open/launch an application by name (e.g. 'notepad')."
    InputModel = OpenAppArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: OpenAppArgs) -> str:
        return f"Open the application '{args.app_name}'."

    def execute(self, args: OpenAppArgs) -> ToolResult:
        key = args.app_name.strip().lower()
        if sys.platform == "win32":
            target = _WINDOWS_APP_ALIASES.get(key, args.app_name)
            try:
                subprocess.Popen(target, shell=True)
            except Exception as exc:  # noqa: BLE001
                return ToolResult.fail(f"Could not open '{args.app_name}': {exc}")
            return ToolResult.ok(f"Launched '{args.app_name}'.")
        # Non-Windows fallback: try to find the executable on PATH.
        exe = shutil.which(key) or shutil.which(args.app_name)
        if not exe:
            return ToolResult.fail(
                f"'{args.app_name}' was not found. App launching by alias is "
                f"Windows-first; on this platform install the app or pass an "
                f"executable on PATH."
            )
        try:
            subprocess.Popen([exe])
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not open '{args.app_name}': {exc}")
        return ToolResult.ok(f"Launched '{exe}'.")


# --------------------------------------------------------------------------- #
# close_app (confirmation)
# --------------------------------------------------------------------------- #
class CloseAppArgs(BaseModel):
    app_name: str = Field(..., description="Name of the app/process to close.")


class CloseAppTool(BaseTool):
    name = "close_app"
    description = "Close an application by name. Requires confirmation."
    InputModel = CloseAppArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True

    def preview(self, args: CloseAppArgs) -> str:
        return (
            f"Close the application '{args.app_name}'. Unsaved work in that app "
            f"may be lost."
        )

    def execute(self, args: CloseAppArgs) -> ToolResult:
        name = args.app_name.strip()
        if sys.platform == "win32":
            image = name if name.lower().endswith(".exe") else f"{name}.exe"
            try:
                result = subprocess.run(
                    ["taskkill", "/IM", image, "/F"],
                    capture_output=True, text=True, timeout=15,
                )
            except Exception as exc:  # noqa: BLE001
                return ToolResult.fail(f"Could not close '{name}': {exc}")
            if result.returncode != 0:
                return ToolResult.fail(
                    f"taskkill failed for '{image}': {result.stderr.strip() or result.stdout.strip()}"
                )
            return ToolResult.ok(f"Closed '{image}'.")
        # Non-Windows fallback using pkill if available.
        if shutil.which("pkill"):
            result = subprocess.run(["pkill", "-f", name], capture_output=True, text=True)
            if result.returncode in (0, 1):
                return ToolResult.ok(f"Sent close signal to processes matching '{name}'.")
            return ToolResult.fail(f"pkill failed: {result.stderr.strip()}")
        return ToolResult.fail("Closing apps is Windows-first; not available on this platform.")


# --------------------------------------------------------------------------- #
# focus_window
# --------------------------------------------------------------------------- #
class FocusWindowArgs(BaseModel):
    window_title: str = Field(..., description="Substring of the window title to focus.")


class FocusWindowTool(BaseTool):
    name = "focus_window"
    description = "Bring a window to the foreground by (partial) title match."
    InputModel = FocusWindowArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: FocusWindowArgs) -> str:
        return f"Focus the window whose title contains '{args.window_title}'."

    def execute(self, args: FocusWindowArgs) -> ToolResult:
        if sys.platform != "win32":
            return ToolResult.fail("Window focus is Windows-only (needs pywinauto).")
        try:
            from pywinauto import Desktop  # type: ignore
        except ImportError:
            return ToolResult.fail(
                "pywinauto is not installed. Run: pip install pywinauto"
            )
        try:
            windows = Desktop(backend="uia").windows()
            for w in windows:
                title = w.window_text()
                if args.window_title.lower() in title.lower():
                    w.set_focus()
                    return ToolResult.ok(f"Focused window: {title}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not focus window: {exc}")
        return ToolResult.fail(f"No window matching '{args.window_title}' found.")


# --------------------------------------------------------------------------- #
# list_open_windows
# --------------------------------------------------------------------------- #
class ListWindowsTool(BaseTool):
    name = "list_open_windows"
    description = "List the titles of currently open top-level windows."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: EmptyArgs) -> str:
        return "List the titles of open windows."

    def execute(self, args: EmptyArgs) -> ToolResult:
        if sys.platform != "win32":
            return ToolResult.fail("Listing windows is Windows-only (needs pywinauto).")
        try:
            from pywinauto import Desktop  # type: ignore
        except ImportError:
            return ToolResult.fail(
                "pywinauto is not installed. Run: pip install pywinauto"
            )
        try:
            titles = [
                w.window_text()
                for w in Desktop(backend="uia").windows()
                if w.window_text()
            ]
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not list windows: {exc}")
        return ToolResult.ok(f"{len(titles)} open window(s).", windows=titles)


def build_app_tools() -> list[BaseTool]:
    return [OpenAppTool(), CloseAppTool(), FocusWindowTool(), ListWindowsTool()]
