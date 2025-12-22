"""Kelly Position DTO

Kelly Position Calculation Result
"""

from typing import TypedDict


class KellyPositionDTO(TypedDict):
    """Kelly Position Calculation Result"""

    symbol: str
    kelly_fraction: float
    adjusted_kelly: float
    position_size: float
    max_position: float
