"""Pivot Stock Status DTO

Pivot Stock vs 60MA Status
"""

from typing import TypedDict


class PivotStockStatusDTO(TypedDict, total=False):
    """Single Pivot Stock Status"""

    current: float
    ma60: float
    vs_ma60: float
    status: str  # "above", "below", "unknown", "error"
