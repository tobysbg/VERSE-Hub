"""Browser automation tools (Phase 4) - driven by a VISIBLE Playwright session.

The browser opens in its own window with a separate profile so the user can
watch every action. Safety is layered:
  * navigation/extraction/screenshots are low risk;
  * clicking and filling fields require confirmation;
  * anything that looks like a login / payment / purchase / booking / form
    submission is escalated to HIGH risk (confirmation, allow-once only), and
    passwords / 2FA / banking data are blocked by the safety manager.

If Playwright isn't installed, every tool returns a clear setup message instead
of doing anything.
"""
from __future__ import annotations

import re
import tempfile

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, EmptyArgs, ToolResult
from .browser_session import BrowserSession, SETUP_HINT, playwright_available

# Text that indicates a submission/login/payment step - stop and confirm.
_SUBMIT_PATTERN = re.compile(
    r"\b(submit|sign\s*in|log\s*in|login|continue|checkout|check\s*out|"
    r"place\s+order|buy|pay|payment|book|reserve|confirm|purchase|"
    r"complete\s+order|next)\b",
    re.I,
)


def _session() -> BrowserSession:
    return BrowserSession.instance()


def _result(ok: bool, payload, ok_msg: str) -> ToolResult:
    if not ok:
        return ToolResult.fail(str(payload))
    return ToolResult.ok(ok_msg, value=payload)


class OpenUrlArgs(BaseModel):
    url: str = Field(..., description="URL to open in the visible browser.")


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Open a URL in the visible automated browser."
    InputModel = OpenUrlArgs
    risk_level = RiskLevel.LOW
    capability = "browser"

    def preview(self, args: OpenUrlArgs) -> str:
        return f"Open {args.url} in the visible browser."

    def execute(self, args: OpenUrlArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().open_url(args.url)
        return _result(ok, payload, f"Opened {args.url} (page title: {payload}).")


class SearchWebArgs(BaseModel):
    query: str = Field(..., description="Web search query.")


class SearchWebTool(BaseTool):
    name = "search_web"
    description = "Run a web search in the visible browser."
    InputModel = SearchWebArgs
    risk_level = RiskLevel.LOW
    capability = "browser"

    def preview(self, args: SearchWebArgs) -> str:
        return f"Search the web for: {args.query}"

    def execute(self, args: SearchWebArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().search_web(args.query)
        return _result(ok, payload, f"Searched for '{args.query}'.")


class ClickTextArgs(BaseModel):
    text: str = Field(..., description="Visible text of the element to click.")


class ClickTextTool(BaseTool):
    name = "click_text"
    description = "Click an element on the current page by its visible text."
    InputModel = ClickTextArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    capability = "browser"

    def dynamic_risk(self, args: ClickTextArgs) -> RiskLevel:
        # Stop before any login/payment/booking/submission step.
        if _SUBMIT_PATTERN.search(args.text):
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    def preview(self, args: ClickTextArgs) -> str:
        note = ""
        if _SUBMIT_PATTERN.search(args.text):
            note = "  (this looks like a submission/login/payment step)"
        return f"Click the element labelled '{args.text}' on the current page.{note}"

    def execute(self, args: ClickTextArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().click_text(args.text)
        return _result(ok, payload, str(payload))


class FillFieldArgs(BaseModel):
    label_or_selector: str = Field(..., description="Field label or CSS selector.")
    value: str = Field(..., description="Value to type into the field.")


class FillFieldTool(BaseTool):
    name = "fill_field"
    description = "Fill a form field with a value on the current page."
    InputModel = FillFieldArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    capability = "browser"

    def preview(self, args: FillFieldArgs) -> str:
        return f"Type '{args.value}' into the field '{args.label_or_selector}'."

    def execute(self, args: FillFieldArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().fill_field(args.label_or_selector, args.value)
        return _result(ok, payload, str(payload))


class ExtractPageTextTool(BaseTool):
    name = "extract_page_text"
    description = "Extract the readable text of the current page."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "browser"

    def preview(self, args: EmptyArgs) -> str:
        return "Extract the visible text of the current page."

    def execute(self, args: EmptyArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().extract_page_text()
        if not ok:
            return ToolResult.fail(str(payload))
        return ToolResult.ok(f"Extracted {len(payload)} characters.", text=payload)


class ScreenshotPageTool(BaseTool):
    name = "screenshot_page"
    description = "Capture a screenshot of the current page."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "browser"

    def preview(self, args: EmptyArgs) -> str:
        return "Take a screenshot of the current browser page."

    def execute(self, args: EmptyArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis_page_", suffix=".png", delete=False)
        tmp.close()
        ok, payload = _session().screenshot_page(tmp.name)
        if not ok:
            return ToolResult.fail(str(payload))
        result = ToolResult.ok(f"Saved page screenshot to {payload}.", path=payload)
        result.screenshot_meta = f"browser page screenshot: {payload}"
        return result


class CloseBrowserTool(BaseTool):
    name = "close_browser"
    description = "Close the automated browser session."
    InputModel = EmptyArgs
    risk_level = RiskLevel.LOW
    capability = "browser"

    def preview(self, args: EmptyArgs) -> str:
        return "Close the automated browser."

    def execute(self, args: EmptyArgs) -> ToolResult:
        if not playwright_available():
            return ToolResult.fail(SETUP_HINT)
        ok, payload = _session().close()
        return _result(ok, payload, str(payload))


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
