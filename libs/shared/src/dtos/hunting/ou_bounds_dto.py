"""Ornstein-Uhlenbeck Mean Reversion Bounds DTO"""

from typing import TypedDict


class OuBoundsDTO(TypedDict):
    """OU Bounds Result"""

    buy_lower: float
    buy_upper: float
    sell_high: float
    sell_extreme: float
    current_deviation_z: float
