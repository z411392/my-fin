"""PerformanceMetrics DTO

Performance Metrics Data Structure
"""

from typing import TypedDict


class PerformanceMetricsDTO(TypedDict, total=False):
    """Performance Metrics"""

    sharpe: float
    num_trials: int
    benchmark_sharpe: float
    annualized_return: float
    volatility: float
    max_drawdown: float
    win_rate: float


class PortfolioConfigDTO(TypedDict, total=False):
    """Portfolio Configuration"""

    positions: list
    benchmark: str
    risk_free_rate: float
