"""Crowding Detection Result DTO"""

from typing import TypedDict


class CrowdingResultDTO(TypedDict):
    """Crowding Result"""

    pairwise_correlation: float
    days_to_cover: float
    dsr: float
    alpha_half_life: float
    status: str
    action: str
