"""Market Regime Result DTO"""

from typing import TypedDict


class RegimeResultDTO(TypedDict):
    """Market Regime Result

    Corresponds to GetRegimePort.execute() return value
    """

    hurst: float
    """Hurst Exponent"""

    hurst_interpretation: str
    """Hurst Interpretation (Trend/Mean Reversion)"""

    hmm_state: int
    """HMM State"""

    hmm_bull_prob: float
    """HMM Bull Probability"""

    regime: str
    """Regime Name"""

    kelly_factor: float
    """Kelly Factor"""

    suggested_strategy: str
    """Suggested Strategy"""
