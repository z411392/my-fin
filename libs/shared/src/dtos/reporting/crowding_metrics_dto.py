"""Crowding Metrics DTO

Crowding Metrics Result
"""

from typing import TypedDict


class CrowdingMetricsDTO(TypedDict):
    """Crowding Metrics Result"""

    crowding_score: float
    crowding_level: str
    short_interest: float
    volume_ratio: float
    recommendation: str
