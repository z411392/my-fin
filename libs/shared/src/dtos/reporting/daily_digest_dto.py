"""Daily Digest Result DTO"""

from typing import TypedDict, NotRequired


class DailyDigestDTO(TypedDict):
    """Daily Digest Result

    Corresponds to GenerateDailyDigestPort.execute() return value
    """

    date: str
    """Date"""

    defcon_level: NotRequired[int]
    """DEFCON Level"""

    vix: NotRequired[float]
    """VIX"""

    market_summary: NotRequired[str]
    """Market Summary"""

    alerts: NotRequired[list[str]]
    """Alert List"""

    email_sent: NotRequired[bool]
    """Whether email sent"""

    is_simulated: NotRequired[bool]
    """Whether simulated mode"""
