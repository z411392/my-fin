"""Kelly Position Calculation Result DTO"""

from typing import TypedDict


class KellyPositionResultDTO(TypedDict):
    """Kelly Position Calculation Result

    Corresponds to CalculateKellyPositionPort.execute() return value
    """

    symbol: str
    """Stock Symbol"""

    vix: float
    """Current VIX Value"""

    vix_tier: str
    """VIX Tier (GREEN/YELLOW/ORANGE/BLACK)"""

    regime: str
    """Market Regime"""

    kelly_pct: float
    """Kelly Percentage"""

    position_size: float
    """Suggested Position Amount"""

    shares: int
    """Suggested Shares"""
