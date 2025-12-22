"""Calendar Event Data Structure"""

from typing import TypedDict


class CalendarEventDTO(TypedDict, total=False):
    """Calendar event

    Used for economic calendar, earnings calendar, etc.
    """

    date: str
    event_type: str
    title: str
    description: str
    importance: str
