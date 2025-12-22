"""美股價格 Fake Adapter"""

from libs.linking.src.ports.us_stock_price_provider_port import (
    USStockPriceProviderPort,
)


class USStockPriceFakeAdapter(USStockPriceProviderPort):
    """美股價格 Fake 實作"""

    def __init__(self) -> None:
        self._close_prices: dict[str, float] = {"NVDA": 150.0, "AMD": 120.0}
        self._daily_returns: dict[str, float] = {"NVDA": 0.03, "AMD": 0.02}

    def get_close_price(self, symbol: str, date: str) -> float:
        return self._close_prices.get(symbol, 100.0)

    def get_daily_return(self, symbol: str, date: str) -> float:
        return self._daily_returns.get(symbol, 0.01)

    # Setters for testing
    def set_daily_return(self, symbol: str, ret: float) -> None:
        self._daily_returns[symbol] = ret
