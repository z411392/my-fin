"""台股價格提供者 Port"""

from typing import Protocol


class TWStockPriceProviderPort(Protocol):
    """台股價格提供者介面"""

    def get_open_price(self, symbol: str, date: str) -> float:
        """取得開盤價"""
        ...

    def get_close_price(self, symbol: str, date: str) -> float:
        """取得收盤價"""
        ...

    def get_daily_return(self, symbol: str, date: str) -> float:
        """取得日報酬"""
        ...
