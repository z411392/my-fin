"""Calendar Raw Data DTO

Calendar raw data structure (loaded from JSON)
"""

from typing import TypedDict


class CalendarRawDataDTO(TypedDict, total=False):
    """Calendar Raw Data (Internal Use)

    Raw structure loaded from economic_calendar.json
    """

    event_types: dict[str, str]
    """Event Type Mapping"""

    fomc_2025: list[str]
    fomc_2026: list[str]
    cpi_2025: list[str]
    cpi_2026: list[str]
    nfp_2025: list[str]
    nfp_2026: list[str]
    # ... Other fields are dynamic keys
