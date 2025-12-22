"""Regime Weights DTO

Regime Weights Result
"""

from typing import TypedDict


class RegimeWeightsDTO(TypedDict):
    """Regime Weights Result"""

    hmm_state: int
    bull_prob: float
    regime: str
    regime_emoji: str
    trend_weight: int
    value_weight: int
    quality_weight: int
