"""Stock List DTO

Stock list (including sector/currency info)
"""

from typing import TypedDict

from libs.shared.src.dtos.catalog.raw_stock_dto import RawStockDTO


class StockItemDTO(TypedDict):
    """Single stock item"""

    code: str
    sector: str
    currency: str


# Type alias for grouped stock list (dynamic keys)
# Key = group name (e.g., "russell_1000", "sox"), Value = list of stocks
GroupedStockList = dict[str, list[StockItemDTO]]

# Type alias for grouped raw stock data (dynamic keys)
# Key = ETF code or group name, Value = list of raw stock dicts
GroupedRawStockList = dict[str, list[RawStockDTO]]

# Type alias for sector proxies (dynamic keys)
# Key = industry code, Value = list of stock codes
SectorProxiesMap = dict[str, list[str]]
