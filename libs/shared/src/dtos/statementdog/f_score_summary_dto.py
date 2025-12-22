"""F-Score Summary DTO"""

from typing import TypedDict


class FScoreSummaryDTO(TypedDict, total=False):
    """F-Score Summary"""

    score: int
    details: dict  # FScoreDTO
