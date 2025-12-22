"""Decision Quality Stats DTO

Decision Quality Statistics
"""

from typing import TypedDict


class DecisionQualityStatsDTO(TypedDict):
    """Decision Quality Statistics (Internal Use)"""

    good_rate: float
    """Good Decision Rate (Percentage)"""
