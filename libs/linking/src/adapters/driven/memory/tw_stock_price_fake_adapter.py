"""台股價格 Fake Adapter"""

from libs.linking.src.ports.tw_stock_price_provider_port import (
    TWStockPriceProviderPort,
)


class TWStockPriceFakeAdapter(TWStockPriceProviderPort):
    """台股價格 Fake 實作"""

    def __init__(self) -> None:
        self._open_prices: dict[str, float] = {"3017": 150.0, "2454": 800.0}
        self._close_prices: dict[str, float] = {"3017": 152.0, "2454": 810.0}
        self._daily_returns: dict[str, float] = {"3017": 0.015, "2454": 0.02}

    def get_open_price(self, symbol: str, date: str) -> float:
        return self._open_prices.get(symbol, 100.0)

    def get_close_price(self, symbol: str, date: str) -> float:
        return self._close_prices.get(symbol, 100.0)

    def get_daily_return(self, symbol: str, date: str) -> float:
        return self._daily_returns.get(symbol, 0.01)

    # Setters for testing
    def set_daily_return(self, symbol: str, ret: float) -> None:
        self._daily_returns[symbol] = ret
