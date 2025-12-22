"""Checkup Result DTO"""

from typing import TypedDict


class CheckupResultDTO(TypedDict, total=False):
    """Health check result"""

    symbol: str
    status: str  # success, failed
    health_grade: str  # A, B, C, D, F
    metrics: dict
    alerts: list
    recommendation: str
    timestamp: str


class DeepCheckupResultDTO(TypedDict, total=False):
    """Deep checkup result"""

    symbol: str
    status: str
    dimensions: list
    overall_grade: str
    alerts: list
    recommendation: str
    email_sent: bool
    timestamp: str


class TriggerExitResultDTO(TypedDict):
    """Trigger exit result"""

    symbol: str
    action: str  # REDUCE, EXIT
    reason: str
    executed: bool
    timestamp: str
