"""Candidate Stock Data Structure

Used as input parameters for Domain Services like sector limit filtering
"""

from typing import TypedDict


class CandidateStockDTO(TypedDict, total=False):
    """Candidate stock data

    Attributes:
        symbol: Stock symbol
        sector: Sector name
        momentum: Momentum score
    """

    symbol: str
    sector: str
    momentum: float
