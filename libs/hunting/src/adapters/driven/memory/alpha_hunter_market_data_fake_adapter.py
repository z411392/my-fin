"""Alpha Hunter Market Data Fake Adapter

模擬 Yahoo Finance API，用於測試
"""

from decimal import Decimal

import numpy as np

from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.shared.src.dtos.market.ohlcv_dto import DailyOhlcvDTO


class AlphaHunterMarketDataFakeAdapter(MarketDataProviderPort):
    """Alpha Hunter Market Data Fake Adapter (模擬 yfinance)"""

    def __init__(self) -> None:
        self._prices: dict[str, list[DailyOhlcvDTO]] = {}
        self._current_prices: dict[str, Decimal] = {
            "^VIX": Decimal("18.5"),
            "SPY": Decimal("450.0"),
            "2330.TW": Decimal("550.0"),
            "2317.TW": Decimal("120.0"),
        }
        self._returns: dict[str, list[float]] = {}
        self._volatility: dict[str, float] = {}

    def set_current_price(self, symbol: str, price: float) -> None:
        """設置現價（測試用）"""
        self._current_prices[symbol] = Decimal(str(price))

    def set_returns(self, symbol: str, returns: list[float]) -> None:
        """設置報酬率（測試用）"""
        self._returns[symbol] = returns

    def set_volatility(self, symbol: str, vol: float) -> None:
        """設置波動率（測試用）"""
        self._volatility[symbol] = vol

    def get_daily_prices(self, symbol: str, days: int = 252) -> list[DailyOhlcvDTO]:
        """取得日級價格資料"""
        if symbol in self._prices:
            return self._prices[symbol][-days:]
        # 產生模擬資料
        base_price = float(self._current_prices.get(symbol, Decimal("100.0")))
        prices = []
        for i in range(days):
            noise = np.random.randn() * 0.02
            price = base_price * (1 + noise)
            prices.append(
                {
                    "date": f"2025-{(i // 30) + 1:02d}-{(i % 30) + 1:02d}",
                    "open": price * 0.99,
                    "high": price * 1.01,
                    "low": price * 0.98,
                    "close": price,
                    "volume": 1000000,
                }
            )
        return prices

    def get_returns(self, symbol: str, days: int = 252) -> list[float]:
        """計算日報酬率"""
        if symbol in self._returns:
            return self._returns[symbol][-days:]
        # 產生模擬報酬率
        return list(np.random.randn(days) * 0.02)

    def get_market_returns(self, days: int = 252) -> list[float]:
        """取得市場 (SPY) 日報酬率"""
        return self.get_returns("SPY", days)

    def get_current_price(self, symbol: str) -> Decimal:
        """取得現價"""
        return self._current_prices.get(symbol, Decimal("100.0"))

    def get_volatility(self, symbol: str, days: int = 20) -> float:
        """計算波動率 (annualized)"""
        if symbol in self._volatility:
            return self._volatility[symbol]
        returns = self.get_returns(symbol, days)
        if len(returns) < 2:
            return 0.0
        return float(np.std(returns) * np.sqrt(252))
