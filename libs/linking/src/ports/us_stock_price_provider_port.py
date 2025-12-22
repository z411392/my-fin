"""美股價格提供者 Port"""

from typing import Protocol


class USStockPriceProviderPort(Protocol):
    """美股價格提供者介面"""

    def get_close_price(self, symbol: str, date: str) -> float:
        """取得收盤價"""
        ...

    def get_daily_return(self, symbol: str, date: str) -> float:
        """取得日報酬"""
        ...
