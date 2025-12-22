"""Pivot Stocks Status Map DTO

Pivot Stock Status Map
"""

from typing import TypedDict
from libs.shared.src.dtos.stock_metrics.pivot_stock_status_dto import (
    PivotStockStatusDTO,
)


class PivotStocksStatusMapDTO(TypedDict):
    """Pivot Stock Status Map (Symbol -> Status)"""

    NVDA: PivotStockStatusDTO
    AAPL: PivotStockStatusDTO
    MSFT: PivotStockStatusDTO
    GOOGL: PivotStockStatusDTO
    AMZN: PivotStockStatusDTO
