"""Raw Stock Data DTO

Raw stock list fetched from TWSE/Wikipedia
"""

from typing import TypedDict


class RawStockDTO(TypedDict, total=False):
    """Raw Stock Data"""

    code: str  # Stock Code
    symbol: str  # Stock Symbol (Alias)
    name: str  # Stock Name
    industry: str  # Industry Category
    sector: str  # Sector Category (Alias)
    market_cap: float  # Market Cap
    currency: str  # Currency
