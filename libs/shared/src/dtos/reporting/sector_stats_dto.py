"""Sector Stats DTO

Sector Statistics Result
"""

from typing import TypedDict


class SectorStatsDTO(TypedDict):
    """Sector Statistics Result"""

    sector: str
    count: int
    avg_zscore: float
    top_stocks: list[str]
