"""Decision Quality DTO

Decision Quality Analysis Structure
"""

from typing import TypedDict, NotRequired


class DecisionQualityDTO(TypedDict, total=False):
    """Decision Quality Analysis (Internal Use)"""

    win_rate: float
    """Win Rate"""

    hold_days_avg: NotRequired[float]
    """Average Holding Days"""

    quality_score: NotRequired[float]
    """Quality Score"""

    correct_direction: NotRequired[int]
    """Correct Direction Count"""

    total_decisions: NotRequired[int]
    """Total Decisions"""

    assessment: NotRequired[str]
    """Assessment Result"""
