"""股票價格 Fake Adapter

實作 StockPriceProviderPort，用於測試
模擬 Yahoo Finance API
"""

from decimal import Decimal

from libs.reviewing.src.ports.stock_price_provider_port import StockPriceProviderPort


class StockPriceFakeAdapter(StockPriceProviderPort):
    """股票價格 Fake Adapter (模擬 yfinance)"""

    def __init__(self) -> None:
        self._prices: dict[str, Decimal] = {
            "2330.TW": Decimal("550.0"),
            "2317.TW": Decimal("120.0"),
            "2454.TW": Decimal("850.0"),
            "AAPL": Decimal("180.0"),
            "NVDA": Decimal("450.0"),
            "^VIX": Decimal("18.5"),
        }

    def set_price(self, symbol: str, price: float) -> None:
        """設置價格（測試用）"""
        self._prices[symbol] = Decimal(str(price))

    def get_current_price(self, symbol: str) -> Decimal:
        """取得股票當前價格"""
        return self._prices.get(symbol, Decimal("100.0"))
