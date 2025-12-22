"""Market Impact Assessment Result DTO"""

from typing import TypedDict


class MarketImpactResultDTO(TypedDict):
    """Market Impact Assessment Result"""

    estimated_impact: float  # Estimated Impact Cost (%)
    order_size: float
    adv: float
    participation_rate: float  # Q/V
    should_execute: bool  # Whether worth executing
