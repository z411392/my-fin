"""CVaR (Conditional Value at Risk) Calculation Result DTO"""

from typing import TypedDict


class CVaRResultDTO(TypedDict):
    """CVaR Calculation Result"""

    var: float  # Value at Risk
    cvar: float  # Conditional VaR (Expected Shortfall)
    confidence_level: float
    tail_ratio: float  # CVaR / VaR, reflecting tail risk
