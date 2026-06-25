"""Email tools (Phase 6) - Gmail via the official API (never screen-clicking).

Read-style operations (count/search/summarize) and draft creation are provided.
Sending is HIGH risk and always requires explicit confirmation. Until the Google
libraries + credentials are configured, each tool returns a clear setup message.
"""
from __future__ import annotations

import base64
from email.mime.text import MIMEText

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, ToolResult
from .google_client import GoogleClient


def _client() -> GoogleClient:
    return GoogleClient()


def _time_range_to_query(time_range: str) -> str:
    tr = (time_range or "").strip().lower()
    mapping = {
        "today": "newer_than:1d",
        "this week": "newer_than:7d",
        "week": "newer_than:7d",
        "this month": "newer_than:30d",
        "month": "newer_than:30d",
        "year": "newer_than:365d",
    }
    if tr in mapping:
        return mapping[tr]
    # Accept "7d", "30d" style ranges directly.
    if tr and tr[0].isdigit() and tr.endswith("d"):
        return f"newer_than:{tr}"
    return "newer_than:7d"


class CountSentArgs(BaseModel):
    time_range: str = Field(default="this week", description="e.g. 'this week', '7d'.")


class CountSentEmailsTool(BaseTool):
    name = "count_sent_emails"
    description = "Count how many emails were sent in a time range."
    InputModel = CountSentArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: CountSentArgs) -> str:
        return f"Count emails sent {args.time_range}."

    def execute(self, args: CountSentArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.gmail()
        if service is None:
            return ToolResult.fail(err)
        query = f"in:sent {_time_range_to_query(args.time_range)}"
        try:
            count = 0
            request = service.users().messages().list(userId="me", q=query, maxResults=500)
            while request is not None:
                resp = request.execute()
                count += len(resp.get("messages", []))
                request = service.users().messages().list_next(request, resp)
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Gmail query failed: {exc}")
        return ToolResult.ok(f"You sent {count} email(s) {args.time_range}.", count=count)


class SearchEmailsArgs(BaseModel):
    query: str = Field(..., description="Gmail search query.")
    max_results: int = Field(default=10, ge=1, le=50)


class SearchEmailsTool(BaseTool):
    name = "search_emails"
    description = "Search the mailbox for messages matching a query."
    InputModel = SearchEmailsArgs
    risk_level = RiskLevel.MEDIUM  # touches personal data

    def preview(self, args: SearchEmailsArgs) -> str:
        return f"Search emails for: {args.query}"

    def execute(self, args: SearchEmailsArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.gmail()
        if service is None:
            return ToolResult.fail(err)
        try:
            resp = service.users().messages().list(
                userId="me", q=args.query, maxResults=args.max_results
            ).execute()
            ids = [m["id"] for m in resp.get("messages", [])]
            results = []
            for mid in ids:
                msg = service.users().messages().get(
                    userId="me", id=mid, format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                results.append({
                    "subject": headers.get("Subject", "(no subject)"),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": msg.get("snippet", ""),
                })
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Gmail search failed: {exc}")
        return ToolResult.ok(f"Found {len(results)} message(s).", messages=results)


class SummarizeEmailsTool(BaseTool):
    name = "summarize_emails"
    description = "Fetch emails matching a query so they can be summarized."
    InputModel = SearchEmailsArgs
    risk_level = RiskLevel.MEDIUM

    def preview(self, args: SearchEmailsArgs) -> str:
        return f"Fetch emails matching '{args.query}' to summarize."

    def execute(self, args: SearchEmailsArgs) -> ToolResult:
        # Reuse the search implementation; the agent's LLM does the summarizing.
        result = SearchEmailsTool().execute(args)
        if not result.success:
            return result
        msgs = result.data.get("messages", [])
        digest = "\n".join(
            f"- {m['subject']} (from {m['from']}): {m['snippet']}" for m in msgs
        )
        return ToolResult.ok(
            f"Fetched {len(msgs)} message(s) for summarization.",
            messages=msgs,
            digest=digest,
        )


class DraftEmailArgs(BaseModel):
    to: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Subject line.")
    body: str = Field(..., description="Email body.")


def _build_raw(to: str, subject: str, body: str) -> str:
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


class DraftEmailTool(BaseTool):
    name = "draft_email"
    description = "Create a draft email (does not send)."
    InputModel = DraftEmailArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: DraftEmailArgs) -> str:
        return f"Draft an email to {args.to} with subject '{args.subject}' (not sent)."

    def execute(self, args: DraftEmailArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.gmail()
        if service is None:
            return ToolResult.fail(err)
        try:
            draft = service.users().drafts().create(
                userId="me",
                body={"message": {"raw": _build_raw(args.to, args.subject, args.body)}},
            ).execute()
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not create draft: {exc}")
        return ToolResult.ok(f"Draft created (id {draft.get('id')}).", draft_id=draft.get("id"))


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email. ALWAYS requires explicit confirmation."
    InputModel = DraftEmailArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    extreme_risk = True

    def preview(self, args: DraftEmailArgs) -> str:
        return f"SEND an email to {args.to}\nSubject: {args.subject}\n\n{args.body}"

    def execute(self, args: DraftEmailArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.gmail()
        if service is None:
            return ToolResult.fail(err)
        try:
            sent = service.users().messages().send(
                userId="me",
                body={"raw": _build_raw(args.to, args.subject, args.body)},
            ).execute()
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not send email: {exc}")
        return ToolResult.ok(f"Email sent to {args.to} (id {sent.get('id')}).", message_id=sent.get("id"))


def build_email_tools() -> list[BaseTool]:
    return [
        CountSentEmailsTool(),
        SearchEmailsTool(),
        SummarizeEmailsTool(),
        DraftEmailTool(),
        SendEmailTool(),
    ]
