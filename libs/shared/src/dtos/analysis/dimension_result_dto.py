"""Dimension Result DTO"""

from typing import TypedDict


class DimensionResultDTO(TypedDict):
    """Dimension Result

    For stock health checkup
    """

    dimension: str
    score: float
    status: str
    detail: str
