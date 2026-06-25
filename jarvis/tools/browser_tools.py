"""Browser automation tools (Phase 4) - safe scaffolding.

These declare full schemas, correct risk levels, and human-readable previews so
the agent and safety layers treat them correctly today. Execution is gated:
until Playwright is installed AND a browser session is started, ``execute``
returns a clear "not available / how to enable" message rather than doing
anything. This satisfies the "safe stub + explain what remains" requirement.

Browser safety rules (enforced here and reinforced in the system prompt):
  * Never buy, book, or submit payment/personal/medical/legal/financial data
    without explicit confirmation.
  * Never bypass CAPTCHAs, store passwords, or auto-enter 2FA codes.
  * Stop before any final booking/payment/submission step.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, EmptyArgs, ToolResult

_PLAYWRIGHT_HINT = (
    "Browser automation is not active yet. To enable it: "
    "`pip install playwright` then `playwright install chromium`. "
    "The browser runs in a separate profile and stops before any "
    "payment/booking/submission step."
)


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


class _BrowserStub(BaseTool):
    """Base for browser tools: gracefully reports the not-yet-active state."""

    capability = "browser"

    def execute(self, args: BaseModel) -> ToolResult:  # type: ignore[override]
        if not _playwright_available():
            return ToolResult.fail(_PLAYWRIGHT_HINT)
        # Playwright is installed but the live session manager is part of a
        # later phase. Report clearly instead of pretending to act.
        return ToolResult.fail(
            "Playwright is installed, but the live browser session is not wired "
            "up in this build. This is a safe stub - no browser action was taken."
        )


class OpenUrlArgs(BaseModel):
    url: str = Field(..., description="URL to open.")


class OpenUrlTool(_BrowserStub):
    name = "open_url"
    description = "Open a URL in the automated browser."
    InputModel = OpenUrlArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: OpenUrlArgs) -> str:
        return f"Open {args.url} in the automated browser."


class SearchWebArgs(BaseModel):
    query: str = Field(..., description="Web search query.")


class SearchWebTool(_BrowserStub):
    name = "search_web"
    description = "Run a web search and return result links."
    InputModel = SearchWebArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: SearchWebArgs) -> str:
        return f"Search the web for: {args.query}"


class ClickTextArgs(BaseModel):
    text: str = Field(..., description="Visible text of the element to click.")


class ClickTextTool(_BrowserStub):
    name = "click_text"
    description = "Click an element on the page by its visible text."
    InputModel = ClickTextArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: ClickTextArgs) -> str:
        return f"Click the element labelled '{args.text}' on the current page."


class FillFieldArgs(BaseModel):
    label_or_selector: str = Field(..., description="Field label or CSS selector.")
    value: str = Field(..., description="Value to type into the field.")


class FillFieldTool(_BrowserStub):
    name = "fill_field"
    description = "Fill a form field with a value."
    InputModel = FillFieldArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: FillFieldArgs) -> str:
        return f"Type '{args.value}' into the field '{args.label_or_selector}'."


class ExtractPageTextTool(_BrowserStub):
    name = "extract_page_text"
    description = "Extract the readable text of the current page."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: EmptyArgs) -> str:
        return "Extract the visible text of the current page."


class ScreenshotPageTool(_BrowserStub):
    name = "screenshot_page"
    description = "Capture a screenshot of the current page."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: EmptyArgs) -> str:
        return "Take a screenshot of the current browser page."


class CloseBrowserTool(_BrowserStub):
    name = "close_browser"
    description = "Close the automated browser session."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: EmptyArgs) -> str:
        return "Close the automated browser."


def build_browser_tools() -> list[BaseTool]:
    return [
        OpenUrlTool(),
        SearchWebTool(),
        ClickTextTool(),
        FillFieldTool(),
        ExtractPageTextTool(),
        ScreenshotPageTool(),
        CloseBrowserTool(),
    ]
