"""Alpha Hunter - Yahoo Finance Market Data Adapter

直接使用 yfinance SDK
"""

from datetime import date, timedelta
from decimal import Decimal
import time

import numpy as np
import yfinance as yf
from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.shared.src.dtos.market.ohlcv_dto import DailyOhlcvDTO


class AlphaHunterMarketDataAdapter(MarketDataProviderPort):
    """Alpha Hunter Market Data Adapter (直接使用 yfinance)"""

    def get_daily_prices(self, symbol: str, days: int = 252) -> list[DailyOhlcvDTO]:
        """取得日級價格資料"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 30)

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            return []

        result = []
        for idx, row in df.iterrows():
            result.append(
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )
        return result

    def get_returns(self, symbol: str, days: int = 252) -> list[float]:
        """計算日報酬率"""
        prices = self.get_daily_prices(symbol, days)
        if len(prices) < 2:
            return []

        returns = []
        for i in range(1, len(prices)):
            prev_close = prices[i - 1]["close"]
            curr_close = prices[i]["close"]
            if prev_close > 0:
                daily_return = (curr_close - prev_close) / prev_close
                returns.append(daily_return)
        return returns

    def get_market_returns(self, days: int = 252) -> list[float]:
        """取得市場 (SPY) 日報酬率"""
        return self.get_returns("SPY", days)

    def get_current_price(self, symbol: str) -> Decimal:
        """取得現價"""
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    return Decimal(str(price))
                return Decimal("0")
            except Exception:
                if attempt < 2:
                    time.sleep(1)
                    continue
                return Decimal("0")
        return Decimal("0")

    def get_volatility(self, symbol: str, days: int = 20) -> float:
        """計算波動率 (annualized)"""
        returns = self.get_returns(symbol, days)
        if len(returns) < 2:
            return 0.0
        return float(np.std(returns) * np.sqrt(252))
