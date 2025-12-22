"""Decision Quality Assessment DTO

Decision Quality Assessment Structure (For Weekly Review)
"""

from typing import TypedDict


class DecisionQualityAssessmentDTO(TypedDict, total=False):
    """Decision Quality Assessment"""

    total_trades: int
    """Total Trades"""

    good_profit: int
    """Good Profit (>5%)"""

    bad_profit: int
    """Bad Profit (0~5%)"""

    good_loss: int
    """Good Loss (-5%~0%)"""

    bad_loss: int
    """Bad Loss (<-5%)"""

    good_decision_rate: float
    """Good Decision Rate"""

    data_source: str
    """Data Source"""
