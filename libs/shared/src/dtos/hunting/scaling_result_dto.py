"""Scaling Result DTO

Volatility Scaling Result
"""

from typing import TypedDict


class ScalingResultDTO(TypedDict):
    """Volatility Scaling Result"""

    original_position: float
    adjusted_position: float
    scaling_factor: float
    action: str
    reason: str
