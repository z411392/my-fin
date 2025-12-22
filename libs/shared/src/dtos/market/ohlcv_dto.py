"""OHLCV Data Structure"""

from typing import TypedDict


class OhlcvDTO(TypedDict):
    """Minute-level OHLCV Data

    Used for real-time market data and minute-level data
    """

    timestamp: str  # ISO 8601 format
    open: float
    high: float
    low: float
    close: float
    volume: int


class DailyOhlcvDTO(TypedDict):
    """Daily OHLCV Data

    Used for historical price data
    """

    date: str  # YYYY-MM-DD format
    open: float
    high: float
    low: float
    close: float
    volume: int
