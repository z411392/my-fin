"""Stock Evaluation DTO

Individual stock evaluation result
"""

from typing import TypedDict


class StockEvaluationResultDTO(TypedDict, total=False):
    """Individual stock evaluation result"""

    symbol: str
    market: str
    zscore: float
    alpha: float
    beta: float
    momentum: float
    quality_score: float
    value_score: float
    signal: str
    recommendation: str


class ScanResultDTO(TypedDict, total=False):
    """Scan result"""

    symbol: str
    rank: int
    zscore: float
    signal: str
    metrics: dict
