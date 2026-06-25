"""Desktop control tools (Phase 5) - real, but OFF by default.

Desktop control (mouse/keyboard/screenshot) is the most powerful capability, so:
  * It is gated behind the ``automation`` capability (the Automation toggle),
    and screenshot/OCR/vision are additionally gated behind ``screen``. The
    registry hides these tools entirely unless the user enables them, so the LLM
    cannot even request them while they're off.
  * Every action is previewed, risk-classified, confirmed where required, and
    written to the action log by the agent loop. The agent loop sets the HUD to
    "Acting" while a tool runs, so control is always visible.
  * pyautogui's fail-safe is enabled: slam the mouse into a screen corner to
    abort. The Stop/Cancel button cancels between steps.
  * No stealth, no background persistence, no auto-elevation. JARVIS warns (in
    diagnostics) if it is running elevated rather than requesting admin.

If pyautogui / mss aren't installed, the tools return a clear setup message.
"""
from __future__ import annotations

import tempfile

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, EmptyArgs, ToolResult

_PYAUTOGUI_HINT = (
    "Desktop control needs pyautogui. Install it with: pip install pyautogui\n"
    "(Automation mode must also be enabled in Settings - it is OFF by default.)"
)
_SCREEN_HINT = (
    "Screen capture needs mss or pyautogui. Install with: pip install mss pyautogui"
)


def _pyautogui():
    """Import pyautogui with the fail-safe enabled, or return None."""
    try:
        import pyautogui  # type: ignore

        pyautogui.FAILSAFE = True  # mouse to a corner aborts
        pyautogui.PAUSE = 0.05
        return pyautogui
    except Exception:  # noqa: BLE001 - missing display/libs can raise non-ImportError
        return None


def _grab_screenshot(path: str) -> tuple[bool, str]:
    """Save a screenshot to ``path`` using mss, falling back to pyautogui."""
    try:
        import mss  # type: ignore
        import mss.tools  # type: ignore

        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=path)
        return True, path
    except Exception:  # noqa: BLE001
        pass
    pg = _pyautogui()
    if pg is None:
        return False, _SCREEN_HINT
    try:
        pg.screenshot(path)
        return True, path
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not capture the screen: {exc}"


# --------------------------------------------------------------------------- #
# screenshot_screen (screen capability)
# --------------------------------------------------------------------------- #
class ScreenshotScreenTool(BaseTool):
    name = "screenshot_screen"
    description = "Capture a screenshot of the screen (requires screen access)."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: EmptyArgs) -> str:
        return "Capture a screenshot of the current screen."

    def execute(self, args: EmptyArgs) -> ToolResult:
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis_screen_", suffix=".png", delete=False)
        tmp.close()
        ok, payload = _grab_screenshot(tmp.name)
        if not ok:
            return ToolResult.fail(payload)
        result = ToolResult.ok(f"Captured screenshot to {payload}.", path=payload)
        result.screenshot_meta = f"screen screenshot: {payload}"
        return result


# --------------------------------------------------------------------------- #
# click
# --------------------------------------------------------------------------- #
class ClickArgs(BaseModel):
    x: int = Field(..., description="Screen X coordinate.")
    y: int = Field(..., description="Screen Y coordinate.")


class ClickTool(BaseTool):
    name = "click"
    description = "Move the mouse to (x, y) and click."
    InputModel = ClickArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    capability = "automation"

    def preview(self, args: ClickArgs) -> str:
        return f"Click the mouse at screen position ({args.x}, {args.y})."

    def execute(self, args: ClickArgs) -> ToolResult:
        pg = _pyautogui()
        if pg is None:
            return ToolResult.fail(_PYAUTOGUI_HINT)
        try:
            pg.click(x=args.x, y=args.y)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Click failed: {exc}")
        return ToolResult.ok(f"Clicked at ({args.x}, {args.y}).")


# --------------------------------------------------------------------------- #
# type_text
# --------------------------------------------------------------------------- #
class TypeTextArgs(BaseModel):
    text: str = Field(..., description="Text to type via the keyboard.")


class TypeTextTool(BaseTool):
    name = "type_text"
    description = "Type text using the keyboard into the focused window."
    InputModel = TypeTextArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    capability = "automation"

    def preview(self, args: TypeTextArgs) -> str:
        preview = args.text if len(args.text) <= 80 else args.text[:77] + "..."
        return f"Type the following text: '{preview}'."

    def execute(self, args: TypeTextArgs) -> ToolResult:
        pg = _pyautogui()
        if pg is None:
            return ToolResult.fail(_PYAUTOGUI_HINT)
        try:
            pg.typewrite(args.text, interval=0.01)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Typing failed: {exc}")
        return ToolResult.ok(f"Typed {len(args.text)} characters.")


# --------------------------------------------------------------------------- #
# press_key
# --------------------------------------------------------------------------- #
class PressKeyArgs(BaseModel):
    key: str = Field(..., description="A single key to press, e.g. 'enter'.")


class PressKeyTool(BaseTool):
    name = "press_key"
    description = "Press a single keyboard key."
    InputModel = PressKeyArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    capability = "automation"

    def preview(self, args: PressKeyArgs) -> str:
        return f"Press the '{args.key}' key."

    def execute(self, args: PressKeyArgs) -> ToolResult:
        pg = _pyautogui()
        if pg is None:
            return ToolResult.fail(_PYAUTOGUI_HINT)
        try:
            pg.press(args.key)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Key press failed: {exc}")
        return ToolResult.ok(f"Pressed '{args.key}'.")


# --------------------------------------------------------------------------- #
# hotkey
# --------------------------------------------------------------------------- #
class HotkeyArgs(BaseModel):
    keys: list[str] = Field(..., description="Keys to press together, e.g. ['ctrl','s'].")


class HotkeyTool(BaseTool):
    name = "hotkey"
    description = "Press a key combination (hotkey)."
    InputModel = HotkeyArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    capability = "automation"

    def preview(self, args: HotkeyArgs) -> str:
        return f"Press the hotkey: {' + '.join(args.keys)}."

    def execute(self, args: HotkeyArgs) -> ToolResult:
        pg = _pyautogui()
        if pg is None:
            return ToolResult.fail(_PYAUTOGUI_HINT)
        if not args.keys:
            return ToolResult.fail("No keys provided.")
        try:
            pg.hotkey(*args.keys)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Hotkey failed: {exc}")
        return ToolResult.ok(f"Pressed {' + '.join(args.keys)}.")


# --------------------------------------------------------------------------- #
# scroll
# --------------------------------------------------------------------------- #
class ScrollArgs(BaseModel):
    amount: int = Field(..., description="Scroll amount; positive=up, negative=down.")


class ScrollTool(BaseTool):
    name = "scroll"
    description = "Scroll the active window by an amount."
    InputModel = ScrollArgs
    risk_level = RiskLevel.LOW
    capability = "automation"

    def preview(self, args: ScrollArgs) -> str:
        direction = "up" if args.amount >= 0 else "down"
        return f"Scroll {direction} by {abs(args.amount)}."

    def execute(self, args: ScrollArgs) -> ToolResult:
        pg = _pyautogui()
        if pg is None:
            return ToolResult.fail(_PYAUTOGUI_HINT)
        try:
            pg.scroll(args.amount)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Scroll failed: {exc}")
        return ToolResult.ok(f"Scrolled by {args.amount}.")


# --------------------------------------------------------------------------- #
# locate_text_on_screen (OCR, screen capability)
# --------------------------------------------------------------------------- #
class LocateTextArgs(BaseModel):
    text: str = Field(..., description="Text to locate on screen via OCR.")


class LocateTextOnScreenTool(BaseTool):
    name = "locate_text_on_screen"
    description = "Find the screen coordinates of given text using OCR (if available)."
    InputModel = LocateTextArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: LocateTextArgs) -> str:
        return f"Locate the text '{args.text}' on screen using OCR."

    def execute(self, args: LocateTextArgs) -> ToolResult:
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:  # noqa: BLE001
            return ToolResult.fail(
                "OCR needs pytesseract + Pillow (and the Tesseract binary). "
                "Install: pip install pytesseract pillow  and install Tesseract."
            )
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis_ocr_", suffix=".png", delete=False)
        tmp.close()
        ok, payload = _grab_screenshot(tmp.name)
        if not ok:
            return ToolResult.fail(payload)
        try:
            data = pytesseract.image_to_data(Image.open(payload), output_type=pytesseract.Output.DICT)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"OCR failed (is Tesseract installed?): {exc}")
        needle = args.text.lower()
        for i, word in enumerate(data.get("text", [])):
            if word and needle in word.lower():
                cx = int(data["left"][i] + data["width"][i] / 2)
                cy = int(data["top"][i] + data["height"][i] / 2)
                return ToolResult.ok(f"Found '{args.text}' at ({cx}, {cy}).", x=cx, y=cy)
        return ToolResult.fail(f"Text '{args.text}' was not found on screen.")


# --------------------------------------------------------------------------- #
# describe_screen (vision LLM - not wired; safe message)
# --------------------------------------------------------------------------- #
class DescribeScreenTool(BaseTool):
    name = "describe_screen"
    description = "Describe what is on screen using a vision model (if configured)."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: EmptyArgs) -> str:
        return "Describe the current screen contents."

    def execute(self, args: EmptyArgs) -> ToolResult:
        return ToolResult.fail(
            "Screen description needs a vision-capable LLM, which is not wired in "
            "this build. A screenshot can still be captured with screenshot_screen."
        )


def build_desktop_tools() -> list[BaseTool]:
    return [
        ScreenshotScreenTool(),
        ClickTool(),
        TypeTextTool(),
        PressKeyTool(),
        HotkeyTool(),
        ScrollTool(),
        LocateTextOnScreenTool(),
        DescribeScreenTool(),
    ]
