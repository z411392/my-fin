"""Pair Trading Opportunity DTO"""

from typing import TypedDict


class PairOpportunityDTO(TypedDict, total=False):
    """Pair Trading Opportunity"""

    leg1: str  # First Leg Stock
    leg2: str  # Second Leg Stock
    spread_zscore: float  # Spread Z-Score
    half_life: float  # Half Life
    correlation: float  # Correlation Coefficient
    signal: str  # Trading Signal
    direction: str  # Trading Direction
