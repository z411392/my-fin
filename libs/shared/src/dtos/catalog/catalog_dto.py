"""Stock Catalog DTO"""

from typing import TypedDict

from libs.shared.src.dtos.catalog.stock_info_dto import StockInfoDTO


class CatalogDTO(TypedDict):
    """Stock Catalog"""

    tw_stocks: list[StockInfoDTO]
    us_stocks: list[StockInfoDTO]
    last_updated: str
