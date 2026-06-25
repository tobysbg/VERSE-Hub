"""Desktop control tools (Phase 5) - safe scaffolding, OFF by default.

Desktop control (mouse/keyboard/screenshot) is the most powerful and dangerous
capability, so it is:
  * gated behind the ``automation`` capability (Automation mode toggle), and
  * additionally gated behind ``screen`` for screenshot/OCR/vision tools.

In this build the tools are safe stubs: they confirm whether the underlying
libraries are present and otherwise report clearly. No clicks, keypresses, or
screenshots are performed. The registry hides these entirely unless the user
explicitly enables Automation mode.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, EmptyArgs, ToolResult

_AUTOMATION_HINT = (
    "Desktop control is a safe stub in this build and performs no action. "
    "Enabling it requires Automation mode ON plus `pip install pyautogui mss`. "
    "Before any real click on an unknown UI element, JARVIS will explain its "
    "intent and ask for confirmation."
)


class _DesktopStub(BaseTool):
    capability = "automation"

    def execute(self, args: BaseModel) -> ToolResult:  # type: ignore[override]
        return ToolResult.fail(_AUTOMATION_HINT)


class ScreenshotScreenTool(_DesktopStub):
    name = "screenshot_screen"
    description = "Capture a screenshot of the screen (requires screen access)."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: EmptyArgs) -> str:
        return "Capture a screenshot of the current screen."


class ClickArgs(BaseModel):
    x: int = Field(..., description="Screen X coordinate.")
    y: int = Field(..., description="Screen Y coordinate.")


class ClickTool(_DesktopStub):
    name = "click"
    description = "Move the mouse to (x, y) and click."
    InputModel = ClickArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True

    def preview(self, args: ClickArgs) -> str:
        return f"Click the mouse at screen position ({args.x}, {args.y})."


class TypeTextArgs(BaseModel):
    text: str = Field(..., description="Text to type via the keyboard.")


class TypeTextTool(_DesktopStub):
    name = "type_text"
    description = "Type text using the keyboard into the focused window."
    InputModel = TypeTextArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: TypeTextArgs) -> str:
        preview = args.text if len(args.text) <= 80 else args.text[:77] + "..."
        return f"Type the following text: '{preview}'."


class PressKeyArgs(BaseModel):
    key: str = Field(..., description="A single key to press, e.g. 'enter'.")


class PressKeyTool(_DesktopStub):
    name = "press_key"
    description = "Press a single keyboard key."
    InputModel = PressKeyArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: PressKeyArgs) -> str:
        return f"Press the '{args.key}' key."


class HotkeyArgs(BaseModel):
    keys: list[str] = Field(..., description="Keys to press together, e.g. ['ctrl','s'].")


class HotkeyTool(_DesktopStub):
    name = "hotkey"
    description = "Press a key combination (hotkey)."
    InputModel = HotkeyArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: HotkeyArgs) -> str:
        return f"Press the hotkey: {' + '.join(args.keys)}."


class ScrollArgs(BaseModel):
    amount: int = Field(..., description="Scroll amount; positive=up, negative=down.")


class ScrollTool(_DesktopStub):
    name = "scroll"
    description = "Scroll the active window by an amount."
    InputModel = ScrollArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: ScrollArgs) -> str:
        direction = "up" if args.amount >= 0 else "down"
        return f"Scroll {direction} by {abs(args.amount)}."


class LocateTextArgs(BaseModel):
    text: str = Field(..., description="Text to locate on screen via OCR.")


class LocateTextOnScreenTool(_DesktopStub):
    name = "locate_text_on_screen"
    description = "Find the screen coordinates of given text using OCR (if available)."
    InputModel = LocateTextArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: LocateTextArgs) -> str:
        return f"Locate the text '{args.text}' on screen using OCR."


class DescribeScreenTool(_DesktopStub):
    name = "describe_screen"
    description = "Describe what is on screen using a vision model (if configured)."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "screen"

    def preview(self, args: EmptyArgs) -> str:
        return "Describe the current screen contents."


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
