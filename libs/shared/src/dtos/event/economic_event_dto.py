"""Economic Event DTO"""

from typing import TypedDict


class EconomicEventDTO(TypedDict, total=False):
    """Economic Event"""

    date: str  # Date (YYYY-MM-DD)
    name: str  # Event Name
    type: str  # Event Type
    risk: str  # Risk Level
    action: str  # Recommended Action
    risk_level: str  # Risk Level (emoji)
