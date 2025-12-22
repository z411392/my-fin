"""Strategy Health DTO

Strategy Health Status Result
"""

from typing import TypedDict


class StrategyHealthDTO(TypedDict):
    """Strategy Health Status Result"""

    health_score: float
    health_level: str
    alpha_decay: float
    factor_exposure: float
    risk_adjusted_return: float
    recommendation: str
    note: str
