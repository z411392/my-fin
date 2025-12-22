"""Event Calendar Result DTO"""

from typing import TypedDict, NotRequired

from libs.shared.src.dtos.event.calendar_event_dto import CalendarEventDTO


class EventCalendarResultDTO(TypedDict):
    """Event Calendar Result

    Corresponds to GetEventsPort.execute() return value
    """

    days: int
    """Query Days"""

    event_type: NotRequired[str | None]
    """Event Type Filter"""

    events: list[CalendarEventDTO]
    """Event List"""

    high_risk_count: int
    """High Risk Event Count"""

    medium_risk_count: int
    """Medium Risk Event Count"""

    suggested_action: str
    """Suggested Action"""

    available_types: NotRequired[list[str] | None]
    """Available Event Types"""
