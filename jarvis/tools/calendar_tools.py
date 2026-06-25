"""Calendar tools (Phase 6) - Google Calendar via the official API.

Listing events and finding free slots are read-only. Creating or deleting events
is HIGH risk and requires explicit confirmation. Until the Google libraries +
credentials are configured, each tool returns a clear setup message.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, ToolResult
from .google_client import GoogleClient


def _client() -> GoogleClient:
    return GoogleClient()


def _range_to_window(date_range: str) -> tuple[datetime, datetime]:
    """Map a loose date range string to a (start, end) UTC window."""
    now = datetime.now(timezone.utc)
    tr = (date_range or "").strip().lower()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if tr in ("today", ""):
        return start, start + timedelta(days=1)
    if tr in ("tomorrow",):
        return start + timedelta(days=1), start + timedelta(days=2)
    if tr in ("this week", "week", "next 7 days", "7 days"):
        return start, start + timedelta(days=7)
    if tr in ("this month", "month", "30 days"):
        return start, start + timedelta(days=30)
    return start, start + timedelta(days=7)


def _rfc3339(dt: datetime) -> str:
    return dt.isoformat()


class DateRangeArgs(BaseModel):
    date_range: str = Field(default="today", description="e.g. 'today', 'next 7 days'.")


class ListEventsTool(BaseTool):
    name = "list_events"
    description = "List calendar events in a date range."
    InputModel = DateRangeArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: DateRangeArgs) -> str:
        return f"List calendar events for {args.date_range}."

    def execute(self, args: DateRangeArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.calendar()
        if service is None:
            return ToolResult.fail(err)
        start, end = _range_to_window(args.date_range)
        try:
            resp = service.events().list(
                calendarId="primary",
                timeMin=_rfc3339(start),
                timeMax=_rfc3339(end),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = []
            for ev in resp.get("items", []):
                start_v = ev.get("start", {})
                events.append({
                    "id": ev.get("id"),
                    "summary": ev.get("summary", "(no title)"),
                    "start": start_v.get("dateTime", start_v.get("date", "")),
                })
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Calendar query failed: {exc}")
        return ToolResult.ok(f"{len(events)} event(s) in range.", events=events)


class FindFreeSlotsTool(BaseTool):
    name = "find_free_slots"
    description = "Find free time slots in a date range (within working hours)."
    InputModel = DateRangeArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: DateRangeArgs) -> str:
        return f"Find free slots for {args.date_range}."

    def execute(self, args: DateRangeArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.calendar()
        if service is None:
            return ToolResult.fail(err)
        start, end = _range_to_window(args.date_range)
        try:
            busy = service.freebusy().query(body={
                "timeMin": _rfc3339(start),
                "timeMax": _rfc3339(end),
                "items": [{"id": "primary"}],
            }).execute()
            periods = busy.get("calendars", {}).get("primary", {}).get("busy", [])
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Free/busy query failed: {exc}")

        # Compute gaps between busy periods inside the requested window.
        free = []
        cursor = start
        for p in periods:
            p_start = datetime.fromisoformat(p["start"].replace("Z", "+00:00"))
            p_end = datetime.fromisoformat(p["end"].replace("Z", "+00:00"))
            if p_start > cursor:
                free.append({"start": _rfc3339(cursor), "end": _rfc3339(p_start)})
            cursor = max(cursor, p_end)
        if cursor < end:
            free.append({"start": _rfc3339(cursor), "end": _rfc3339(end)})
        return ToolResult.ok(f"Found {len(free)} free slot(s).", free_slots=free)


class CreateEventArgs(BaseModel):
    title: str = Field(..., description="Event title.")
    start: str = Field(..., description="Start date/time (ISO 8601).")
    end: str = Field(..., description="End date/time (ISO 8601).")
    description: str = Field(default="", description="Optional event description.")


class CreateEventTool(BaseTool):
    name = "create_event"
    description = "Create a calendar event. Requires confirmation."
    InputModel = CreateEventArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True

    def preview(self, args: CreateEventArgs) -> str:
        return f"Create event '{args.title}' from {args.start} to {args.end}."

    def execute(self, args: CreateEventArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.calendar()
        if service is None:
            return ToolResult.fail(err)
        try:
            event = service.events().insert(calendarId="primary", body={
                "summary": args.title,
                "description": args.description,
                "start": {"dateTime": args.start},
                "end": {"dateTime": args.end},
            }).execute()
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not create event: {exc}")
        return ToolResult.ok(f"Created event '{args.title}'.", event_id=event.get("id"))


class DeleteEventArgs(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete.")


class DeleteEventTool(BaseTool):
    name = "delete_event"
    description = "Delete a calendar event. Requires confirmation."
    InputModel = DeleteEventArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    extreme_risk = True

    def preview(self, args: DeleteEventArgs) -> str:
        return f"DELETE calendar event with id '{args.event_id}'."

    def execute(self, args: DeleteEventArgs) -> ToolResult:
        client = _client()
        if not client.available():
            return ToolResult.fail(client.setup_message())
        service, err = client.calendar()
        if service is None:
            return ToolResult.fail(err)
        try:
            service.events().delete(calendarId="primary", eventId=args.event_id).execute()
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not delete event: {exc}")
        return ToolResult.ok(f"Deleted event {args.event_id}.")


def build_calendar_tools() -> list[BaseTool]:
    return [
        ListEventsTool(),
        FindFreeSlotsTool(),
        CreateEventTool(),
        DeleteEventTool(),
    ]
