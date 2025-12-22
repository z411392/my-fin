"""Event Calendar Result DTO"""

from typing import TypedDict


class EventCalendarUpdateResultDTO(TypedDict, total=False):
    """Event Calendar Update Result"""

    status: str  # success, failed
    month: int
    year: int
    events_count: int
    message: str


class RegimeChangeResultDTO(TypedDict, total=False):
    """Regime Change Detection Result"""

    current_regime: int  # 0=Bear, 1=Bull
    previous_regime: int
    changed: bool
    bull_prob: float
    message: str


class ReferenceDataSyncResultDTO(TypedDict, total=False):
    """Reference Data Sync Result"""

    status: str
    scope: str
    synced_items: int
    failed_items: int
    message: str
