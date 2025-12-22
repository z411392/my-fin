"""Recommendation Target DTO"""

from typing import TypedDict


class RecommendationDTO(TypedDict):
    """Recommendation Target"""

    symbol: str
    name: str
    market: str  # "tw" or "us"
    score: float  # Composite Score
    rank: int  # Rank
    reason: str  # Recommendation Reason
    checkup_sent: bool  # Whether checkup report sent
