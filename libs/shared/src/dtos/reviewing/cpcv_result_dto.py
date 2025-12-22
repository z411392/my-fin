"""CPCV (Combinatorial Purged Cross-Validation) Result DTO"""

from typing import TypedDict


class CPCVResultDTO(TypedDict):
    """CPCV Validation Result"""

    sharpe_distribution: list[float]  # Sharpe Ratio of each fold
    mean_sharpe: float
    std_sharpe: float
    failure_probability: float  # P(Sharpe < 0)
    is_valid: bool  # Whether valid
