"""Portfolio Health DTO

Portfolio Health Result
"""

from typing import TypedDict


class PortfolioHealthDTO(TypedDict):
    """Portfolio Health Result"""

    healthy_count: int
    warning_count: int
    critical_count: int
    total_count: int
    health_rate: float
    status: str
    issues: list[str]
