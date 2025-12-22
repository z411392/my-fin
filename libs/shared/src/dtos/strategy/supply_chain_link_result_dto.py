"""Supply Chain Link Analysis Result DTO"""

from typing import TypedDict, NotRequired


class SupplyChainLinkResultDTO(TypedDict):
    """Supply Chain Link Analysis Result

    Corresponds to GetSupplyChainLinkPort.execute() return value
    """

    us_symbol: str
    """US Stock Symbol"""

    tw_symbol: str
    """TW Stock Symbol"""

    beta: float
    """Kalman Beta"""

    lag: int
    """Lag Days"""

    correlation: float
    """Correlation Coefficient"""

    expected_move: float
    """Expected Move"""

    signal: str
    """Signal (EXECUTE/SHORT/REDUCE/ABORT/NEUTRAL/NO_DATA)"""

    sample_size: NotRequired[int]
    """Sample Size"""

    period: NotRequired[str]
    """Data Period"""

    tw_prev_close: NotRequired[float | None]
    """TW Stock Previous Close Price"""

    tw_open: NotRequired[float | None]
    """TW Stock Open Price"""

    tw_current: NotRequired[float | None]
    """TW Stock Current Price"""

    target_price: NotRequired[float | None]
    """Theoretical Target Price"""

    remaining_alpha: NotRequired[float | None]
    """Remaining Alpha"""
