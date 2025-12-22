"""Decision Quality DTO

Decision Quality Result
"""

from typing import TypedDict


class DecisionQualityDTO(TypedDict):
    """Decision Quality Result"""

    quality_score: float
    quality_level: str
    correct_entries: int
    total_entries: int
    timing_score: float
    note: str
