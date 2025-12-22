"""Earnings Quality Metrics DTO"""

from typing import TypedDict


class EarningsQualityDTO(TypedDict, total=False):
    """Earnings Quality Metrics"""

    symbol: str
    cfo: float  # Operating Cash Flow
    net_income: float  # Net Income
    cfo_ni_ratio: float  # CFO / NI Ratio
    fcf_ttm: float  # Free Cash Flow TTM
    is_quality: bool  # Whether Quality is Good
