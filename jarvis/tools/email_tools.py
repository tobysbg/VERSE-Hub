"""Email tools (Phase 6) - safe scaffolding for Gmail.

Read-only style operations (count/search/summarize) and draft creation are
provided as interfaces. Any operation that SENDS, deletes, archives, or
forwards mail is HIGH risk and always requires explicit confirmation.

Until Gmail OAuth credentials are configured, ``execute`` reports the setup
steps rather than touching a mailbox.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, ToolResult

_GMAIL_HINT = (
    "Gmail is not configured. To enable email tools: create a Google Cloud "
    "OAuth client, enable the Gmail API, and place credentials.json next to the "
    "app, then authorize on first use. Sending/deleting always require "
    "explicit confirmation."
)


class _EmailStub(BaseTool):
    def execute(self, args: BaseModel) -> ToolResult:  # type: ignore[override]
        return ToolResult.fail(_GMAIL_HINT)


class CountSentArgs(BaseModel):
    time_range: str = Field(default="this week", description="e.g. 'this week', '7d'.")


class CountSentEmailsTool(_EmailStub):
    name = "count_sent_emails"
    description = "Count how many emails were sent in a time range."
    InputModel = CountSentArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: CountSentArgs) -> str:
        return f"Count emails sent {args.time_range}."


class SearchEmailsArgs(BaseModel):
    query: str = Field(..., description="Gmail search query.")


class SearchEmailsTool(_EmailStub):
    name = "search_emails"
    description = "Search the mailbox for messages matching a query."
    InputModel = SearchEmailsArgs
    risk_level = RiskLevel.MEDIUM  # touches personal data

    def preview(self, args: SearchEmailsArgs) -> str:
        return f"Search emails for: {args.query}"


class SummarizeEmailsTool(_EmailStub):
    name = "summarize_emails"
    description = "Summarize emails matching a query."
    InputModel = SearchEmailsArgs
    risk_level = RiskLevel.MEDIUM

    def preview(self, args: SearchEmailsArgs) -> str:
        return f"Summarize emails matching: {args.query}"


class DraftEmailArgs(BaseModel):
    to: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Subject line.")
    body: str = Field(..., description="Email body.")


class DraftEmailTool(_EmailStub):
    name = "draft_email"
    description = "Create a draft email (does not send)."
    InputModel = DraftEmailArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: DraftEmailArgs) -> str:
        return f"Draft an email to {args.to} with subject '{args.subject}' (not sent)."


class SendEmailTool(_EmailStub):
    name = "send_email"
    description = "Send an email. ALWAYS requires explicit confirmation."
    InputModel = DraftEmailArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    extreme_risk = True

    def preview(self, args: DraftEmailArgs) -> str:
        return (
            f"SEND an email to {args.to}\nSubject: {args.subject}\n\n{args.body}"
        )


def build_email_tools() -> list[BaseTool]:
    return [
        CountSentEmailsTool(),
        SearchEmailsTool(),
        SummarizeEmailsTool(),
        DraftEmailTool(),
        SendEmailTool(),
    ]
