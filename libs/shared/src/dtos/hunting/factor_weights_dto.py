"""Factor Weights DTO

HMM Regime Factor Weights
"""

from typing import TypedDict


class FactorWeightsDTO(TypedDict):
    """Factor Weights Result"""

    trend: float
    value: float
    quality: float
    regime: str
    regime_emoji: str
