"""DSR Result DTO

Deflated Sharpe Ratio Result
"""

from typing import TypedDict


class DSRResultDTO(TypedDict):
    """DSR Result"""

    sharpe: float
    dsr: float
    psr: float
    interpretation: str


class PerformanceSummaryDTO(TypedDict, total=False):
    """Performance Summary"""

    days: int
    total_return: float
    annualized_return: float
    volatility: float
    sharpe: float
    dsr: float
    psr: float
    interpretation: str
    max_drawdown: float
    win_rate: float
    error: str
    data_points: int
