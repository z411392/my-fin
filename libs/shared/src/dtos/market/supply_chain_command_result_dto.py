"""Supply Chain Command Result DTO"""

from typing import TypedDict


class DailyBetaResultDTO(TypedDict, total=False):
    """Daily Beta Calculation Result"""

    us_symbol: str
    tw_symbol: str
    kalman_beta: float
    lookback: int
    timestamp: str


class SupplyChainMapUpdateResultDTO(TypedDict, total=False):
    """Supply Chain Map Update Result"""

    status: str  # success, failed
    updated_count: int
    message: str
