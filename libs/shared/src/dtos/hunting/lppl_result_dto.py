"""LPPL Critical Time Estimation Result DTO"""

from typing import TypedDict


class LpplResultDTO(TypedDict, total=False):
    """LPPL Bubble Detection Result"""

    is_bubble: float
    critical_time_days: float
    acceleration: float
    velocity: float
