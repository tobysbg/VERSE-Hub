"""Calendar tools (Phase 6) - safe scaffolding for Google Calendar.

Listing events and finding free slots are read-only. Creating or deleting
events requires explicit confirmation. Until credentials are configured,
``execute`` reports the setup steps instead of touching a calendar.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, ToolResult

_CAL_HINT = (
    "Google Calendar is not configured. Enable the Google Calendar API, add an "
    "OAuth client, place credentials.json next to the app, and authorize on "
    "first use. Creating/deleting events always require confirmation."
)


class _CalendarStub(BaseTool):
    def execute(self, args: BaseModel) -> ToolResult:  # type: ignore[override]
        return ToolResult.fail(_CAL_HINT)


class DateRangeArgs(BaseModel):
    date_range: str = Field(default="today", description="e.g. 'today', 'next 7 days'.")


class ListEventsTool(_CalendarStub):
    name = "list_events"
    description = "List calendar events in a date range."
    InputModel = DateRangeArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: DateRangeArgs) -> str:
        return f"List calendar events for {args.date_range}."


class FindFreeSlotsTool(_CalendarStub):
    name = "find_free_slots"
    description = "Find free time slots in a date range."
    InputModel = DateRangeArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: DateRangeArgs) -> str:
        return f"Find free slots for {args.date_range}."


class CreateEventArgs(BaseModel):
    title: str = Field(..., description="Event title.")
    start: str = Field(..., description="Start date/time (ISO 8601).")
    end: str = Field(..., description="End date/time (ISO 8601).")
    description: str = Field(default="", description="Optional event description.")


class CreateEventTool(_CalendarStub):
    name = "create_event"
    description = "Create a calendar event. Requires confirmation."
    InputModel = CreateEventArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True

    def preview(self, args: CreateEventArgs) -> str:
        return f"Create event '{args.title}' from {args.start} to {args.end}."


class DeleteEventArgs(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete.")


class DeleteEventTool(_CalendarStub):
    name = "delete_event"
    description = "Delete a calendar event. Requires confirmation."
    InputModel = DeleteEventArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    extreme_risk = True

    def preview(self, args: DeleteEventArgs) -> str:
        return f"DELETE calendar event with id '{args.event_id}'."


def build_calendar_tools() -> list[BaseTool]:
    return [
        ListEventsTool(),
        FindFreeSlotsTool(),
        CreateEventTool(),
        DeleteEventTool(),
    ]
