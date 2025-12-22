"""Performance DTO

Performance Result
"""

from typing import TypedDict


class PerformanceDTO(TypedDict):
    """Performance Result"""

    total_return: float
    benchmark_return: float
    alpha: float
    beta: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    note: str
