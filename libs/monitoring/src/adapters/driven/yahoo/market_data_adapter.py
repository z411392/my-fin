"""Risk Sentinel - Yahoo Finance Market Data Adapter

直接使用 yfinance SDK，實作 MarketDataProviderPort
"""

from datetime import date, timedelta
from decimal import Decimal
import time

import yfinance as yf
from libs.monitoring.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.shared.src.dtos.market.ohlcv_dto import DailyOhlcvDTO, OhlcvDTO
from libs.shared.src.dtos.market.options_chain_dto import OptionsChainDTO
from libs.shared.src.dtos.stock_metrics.pivot_stocks_status_map_dto import (
    PivotStocksStatusMapDTO,
)


class YahooMarketDataAdapter(MarketDataProviderPort):
    """Market Data Adapter using Yahoo Finance

    直接使用 yfinance SDK，無中間層
    """

    def get_vix(self) -> Decimal:
        """取得 VIX 指數"""
        price = self._get_current_price("^VIX")
        return price if price > 0 else Decimal("15.0")

    def get_price(self, symbol: str) -> Decimal:
        """取得現價"""
        return self._get_current_price(symbol)

    def get_daily_prices(self, symbol: str, days: int = 60) -> list[DailyOhlcvDTO]:
        """取得日級價格資料"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self._get_daily_ohlcv(symbol, start_date, end_date)

    def get_intraday_data(self, symbol: str, interval: str = "1m") -> list[OhlcvDTO]:
        """取得盤中資料"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval=interval)

        if df.empty:
            return []

        result = []
        for idx, row in df.iterrows():
            result.append(
                {
                    "datetime": idx.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )
        return result

    def get_options_chain(self, symbol: str) -> OptionsChainDTO:
        """取得選擇權鏈"""
        ticker = yf.Ticker(symbol)
        try:
            expirations = ticker.options
            if not expirations:
                return {"calls": [], "puts": [], "expiration": None}

            nearest_exp = expirations[0]
            chain = ticker.option_chain(nearest_exp)

            calls = []
            for _, row in chain.calls.iterrows():
                calls.append(
                    {
                        "strike": float(row["strike"]),
                        "lastPrice": float(row["lastPrice"]),
                        "bid": float(row["bid"]),
                        "ask": float(row["ask"]),
                        "volume": int(row["volume"]) if row["volume"] else 0,
                        "openInterest": int(row["openInterest"])
                        if row["openInterest"]
                        else 0,
                        "impliedVolatility": float(row["impliedVolatility"]),
                    }
                )

            puts = []
            for _, row in chain.puts.iterrows():
                puts.append(
                    {
                        "strike": float(row["strike"]),
                        "lastPrice": float(row["lastPrice"]),
                        "bid": float(row["bid"]),
                        "ask": float(row["ask"]),
                        "volume": int(row["volume"]) if row["volume"] else 0,
                        "openInterest": int(row["openInterest"])
                        if row["openInterest"]
                        else 0,
                        "impliedVolatility": float(row["impliedVolatility"]),
                    }
                )

            return {
                "expiration": nearest_exp,
                "calls": calls,
                "puts": puts,
            }
        except Exception:
            return {"calls": [], "puts": [], "expiration": None}

    def get_pivot_stocks_status(self) -> PivotStocksStatusMapDTO:
        """檢查樞紐股 vs 60MA 狀態"""
        pivot_stocks = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN"]
        result = {}

        for symbol in pivot_stocks:
            try:
                prices = self.get_daily_prices(symbol, days=70)
                if len(prices) < 60:
                    result[symbol] = {"status": "unknown", "vs_ma60": 0}
                    continue

                current_price = float(prices[-1]["close"])
                ma60 = sum(p["close"] for p in prices[-60:]) / 60
                vs_ma60 = (current_price - ma60) / ma60 * 100

                result[symbol] = {
                    "current": current_price,
                    "ma60": round(ma60, 2),
                    "vs_ma60": round(vs_ma60, 2),
                    "status": "above" if current_price > ma60 else "below",
                }
            except Exception:
                result[symbol] = {"status": "error", "vs_ma60": 0}

        return result

    def _get_current_price(self, symbol: str, max_retries: int = 3) -> Decimal:
        """取得現價 (帶重試機制)"""
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    return Decimal(str(price))

                info = ticker.info
                price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
                return Decimal(str(price))

            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return Decimal("0")

        return Decimal("0")

    def _get_daily_ohlcv(
        self, symbol: str, start_date: date, end_date: date
    ) -> list[DailyOhlcvDTO]:
        """取得日級 OHLCV 數據"""
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
