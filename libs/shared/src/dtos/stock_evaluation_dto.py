"""Evaluation Result DTO

Stock evaluation result data structure
"""

from typing import TypedDict


class StockEvaluationDTO(TypedDict, total=False):
    """Stock evaluation result (from _evaluate_stock_multi_factor)"""

    symbol: str  # Stock symbol
    name: str | None  # Stock name
    sector: str | None  # Sector ETF
    open: float | None  # Open price
    high: float | None  # High price
    low: float | None  # Low price
    close: float | None  # Close price
    prev_close: float | None  # Previous close price
    volume: int | None  # Volume
    daily_return: float | None  # Daily return (%)
