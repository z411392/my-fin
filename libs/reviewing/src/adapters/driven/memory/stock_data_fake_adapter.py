"""股票資料 Fake Adapter

實作 StockDataProviderPort，用於測試
模擬 Yahoo Finance API
"""

from decimal import Decimal

import numpy as np

from libs.reviewing.src.ports.stock_data_provider_port import StockDataProviderPort


class StockDataFakeAdapter(StockDataProviderPort):
    """股票資料 Fake Adapter (模擬 yfinance)"""

    def __init__(self) -> None:
        self._returns_matrix: np.ndarray | None = None
        self._volumes: dict[str, float] = {}
        self._prices: dict[str, Decimal] = {
            "2330.TW": Decimal("550.0"),
            "2317.TW": Decimal("120.0"),
            "AAPL": Decimal("180.0"),
        }

    def set_returns_matrix(self, matrix: np.ndarray) -> None:
        """設置報酬矩陣（測試用）"""
        self._returns_matrix = matrix

    def set_volume(self, symbol: str, volume: float) -> None:
        """設置日均成交量（測試用）"""
        self._volumes[symbol] = volume

    def set_price(self, symbol: str, price: float) -> None:
        """設置價格（測試用）"""
        self._prices[symbol] = Decimal(str(price))

    def get_returns_matrix(
        self,
        symbols: list[str],
        days: int = 252,
    ) -> np.ndarray:
        """取得多標的報酬矩陣"""
        if self._returns_matrix is not None:
            return self._returns_matrix
        # 產生模擬資料
        n_symbols = len(symbols)
        return np.random.randn(days, n_symbols) * 0.02

    def get_average_daily_volume(
        self,
        symbol: str,
        days: int = 20,
    ) -> float:
        """取得平均日成交量"""
        return self._volumes.get(symbol, 1000000.0)

    def get_current_price(self, symbol: str) -> Decimal:
        """取得現價"""
        return self._prices.get(symbol, Decimal("100.0"))
