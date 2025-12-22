"""Earnings Data Structure"""

from typing import TypedDict


class EarningsDTO(TypedDict):
    """Earnings Data

    For historical earnings queries
    """

    date: str
    eps_estimate: float
    eps_actual: float
    surprise: float
    surprise_pct: float
