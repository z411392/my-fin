"""Valuation Metrics DTO"""

from typing import TypedDict


class ValuationMetricsDTO(TypedDict, total=False):
    """Valuation Metrics"""

    symbol: str
    current_pe: float
    pe_percentile_5: float
    pe_percentile_25: float
    pe_percentile_50: float
    pe_percentile_75: float
    pe_percentile_95: float
    is_safe: bool  # Whether within margin of safety
