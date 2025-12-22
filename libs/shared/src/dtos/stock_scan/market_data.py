"""Market Data DTO (from yfinance)"""

from typing import TypedDict


class MarketData(TypedDict, total=False):
    """Market Data (from yfinance)"""

    name: str | None  # Stock Full Name
    sector: str | None  # Industry ETF
    open: float | None  # Today Open
    high: float | None  # Today High
    low: float | None  # Today Low
    close: float | None  # Today Close
    prev_close: float | None  # Previous Close
    volume: int | None  # Volume
    daily_return: float | None  # Daily Return (%)
