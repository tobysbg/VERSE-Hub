"""A persistent, VISIBLE Playwright browser session (Phase 4).

Design notes
------------
* The browser is launched **headed** (``headless=False``) in a **separate,
  persistent profile** under ``~/.jarvis/browser_profile`` so the user can watch
  every action and the agent never touches the user's real browser profile.
* Playwright's sync API is thread-affine: all calls must happen on the thread
  that created it. Agent requests run on short-lived worker threads, so this
  module owns a single long-lived background thread that holds the Playwright
  objects. Tools submit callables to that thread and block for the result, which
  keeps one visible browser alive across many requests.
* Everything is lazy and defensive: if Playwright (or its browser binary) isn't
  installed, the session reports a clear setup message and no tool ever crashes.

Safety is enforced one layer up (the tools declare risk levels and the safety
manager requires confirmation before any submission/login/payment/etc.). This
module only performs the low-level, already-approved action.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

_PROFILE_DIR = Path.home() / ".jarvis" / "browser_profile"

# Visible (not headless) - the user must be able to watch the automation.
VISIBLE_MODE = True


def playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def chromium_installed() -> bool:
    """Best-effort: is the Playwright Chromium browser binary present?"""
    if not playwright_available():
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            path = pw.chromium.executable_path
        return bool(path) and os.path.exists(path)
    except Exception:  # noqa: BLE001
        return False


def _install_commands() -> str:
    """Setup commands qualified with the EXACT interpreter running JARVIS.

    The most common failure is installing Playwright into a different venv than
    the one launching JARVIS; naming the interpreter makes that obvious.
    """
    exe = sys.executable
    return (
        f'    "{exe}" -m pip install playwright\n'
        f'    "{exe}" -m playwright install chromium'
    )


SETUP_HINT = (
    "Browser automation needs Playwright, which isn't usable in the interpreter "
    "running JARVIS.\n"
    f"Running interpreter: {sys.executable}\n"
    "Install it into THIS interpreter:\n"
    f"{_install_commands()}\n"
    "The browser opens in a separate, visible window using its own profile, and "
    "JARVIS stops for confirmation before any login, payment, booking, or form "
    "submission."
)


class _Command:
    __slots__ = ("fn", "done", "result", "error")

    def __init__(self, fn: Callable[[Any], Any]) -> None:
        self.fn = fn
        self.done = threading.Event()
        self.result: Any = None
        self.error: Optional[str] = None


class BrowserSession:
    """Singleton wrapper around a visible Playwright Chromium context."""

    _instance: Optional["BrowserSession"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._queue: "queue.Queue[Optional[_Command]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._started = False
        self._start_error: Optional[str] = None

    @classmethod
    def instance(cls) -> "BrowserSession":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # -- lifecycle -----------------------------------------------------------
    def available(self) -> bool:
        return playwright_available()

    def ensure_started(self) -> Tuple[bool, str]:
        """Start the browser thread if needed. Returns (ok, error_message)."""
        if not self.available():
            return False, SETUP_HINT
        if self._started:
            return True, ""
        ready = threading.Event()

        def _runner() -> None:
            self._run(ready)

        self._thread = threading.Thread(target=_runner, name="jarvis-browser", daemon=True)
        self._thread.start()
        ready.wait(timeout=60)
        if self._start_error:
            return False, self._start_error
        return self._started, ""

    def _run(self, ready: threading.Event) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # noqa: BLE001
            self._start_error = f"Playwright import failed: {exc}"
            ready.set()
            return

        try:
            _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=str(_PROFILE_DIR),
                    headless=False,  # VISIBLE so the user can watch
                    args=["--start-maximized"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                self._started = True
                ready.set()

                # Command loop - everything Playwright happens on THIS thread.
                while True:
                    cmd = self._queue.get()
                    if cmd is None:  # shutdown sentinel
                        break
                    try:
                        cmd.result = cmd.fn(page)
                    except Exception as exc:  # noqa: BLE001
                        cmd.error = str(exc)
                    finally:
                        cmd.done.set()

                try:
                    context.close()
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            self._start_error = (
                f"Could not launch Chromium ({exc}). If this is the first run, "
                f"the browser binary is probably missing - install it with:\n"
                f"{_install_commands()}"
            )
            ready.set()
        finally:
            self._started = False

    def _submit(self, fn: Callable[[Any], Any]) -> Tuple[bool, Any]:
        ok, err = self.ensure_started()
        if not ok:
            return False, err
        cmd = _Command(fn)
        self._queue.put(cmd)
        cmd.done.wait()
        if cmd.error is not None:
            return False, cmd.error
        return True, cmd.result

    # -- high-level operations (each returns (ok, data_or_error)) ------------
    def open_url(self, url: str) -> Tuple[bool, Any]:
        if "://" not in url:
            url = "https://" + url
        return self._submit(lambda page: (page.goto(url, wait_until="domcontentloaded"), page.title())[1])

    def search_web(self, query: str) -> Tuple[bool, Any]:
        from urllib.parse import quote_plus

        url = f"https://duckduckgo.com/?q={quote_plus(query)}"
        return self._submit(lambda page: (page.goto(url, wait_until="domcontentloaded"), page.title())[1])

    def click_text(self, text: str) -> Tuple[bool, Any]:
        def _fn(page):
            page.get_by_text(text, exact=False).first.click(timeout=8000)
            return f"Clicked '{text}'."
        return self._submit(_fn)

    def fill_field(self, label_or_selector: str, value: str) -> Tuple[bool, Any]:
        def _fn(page):
            try:
                page.get_by_label(label_or_selector, exact=False).first.fill(value, timeout=4000)
            except Exception:  # noqa: BLE001 - fall back to a CSS/placeholder selector
                page.locator(label_or_selector).first.fill(value, timeout=4000)
            return f"Filled '{label_or_selector}'."
        return self._submit(_fn)

    def extract_page_text(self) -> Tuple[bool, Any]:
        return self._submit(lambda page: (page.inner_text("body") or "")[:8000])

    def screenshot_page(self, path: str) -> Tuple[bool, Any]:
        def _fn(page):
            page.screenshot(path=path, full_page=False)
            return path
        return self._submit(_fn)

    def current_url(self) -> Tuple[bool, Any]:
        return self._submit(lambda page: page.url)

    def close(self) -> Tuple[bool, Any]:
        if not self._started:
            return True, "Browser was not running."
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=10)
        self._started = False
        return True, "Browser closed."


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #
def browser_tools_registered() -> bool:
    """True if the visible browser tools are present in the default registry."""
    try:
        from .registry import build_default_registry

        names = {t.name for t in build_default_registry().all()}
        return {"open_url", "search_web", "extract_page_text"} <= names
    except Exception:  # noqa: BLE001
        return False


def browser_diagnostics(check_chromium: bool = True) -> dict:
    """Snapshot of the browser environment for the diagnostics panel/log."""
    pw_ok = playwright_available()
    return {
        "executable": sys.executable,
        "playwright_import_ok": pw_ok,
        "chromium_installed": chromium_installed() if (pw_ok and check_chromium) else False,
        "browser_tools_registered": browser_tools_registered(),
        "visible_mode": VISIBLE_MODE,
    }


def format_browser_diagnostics(diag: dict) -> str:
    def yn(flag: bool) -> str:
        return "yes" if flag else "no"

    return "\n".join([
        f"playwright import ok    : {yn(diag['playwright_import_ok'])}",
        f"chromium installed      : {yn(diag['chromium_installed'])}",
        f"browser tools registered: {yn(diag['browser_tools_registered'])}",
        f"visible (not headless)  : {yn(diag['visible_mode'])}",
        f"interpreter             : {diag['executable']}",
    ])
