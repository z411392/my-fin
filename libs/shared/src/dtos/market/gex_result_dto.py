"""GEX Calculation Result DTO"""

from typing import TypedDict, NotRequired


class GEXResultDTO(TypedDict):
    """GEX (Gamma Exposure) calculation result"""

    gex: float
    """GEX value"""

    level: NotRequired[str]
    """GEX level (POSITIVE/NEUTRAL/NEGATIVE)"""

    flip_point: NotRequired[float]
    """Flip point"""

    symbol: NotRequired[str]
    """Symbol"""
