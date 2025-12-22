"""即時市場數據 Yahoo Adapter

使用 yfinance 獲取分鐘級數據和選擇權鏈
"""

import yfinance as yf
from libs.monitoring.src.ports.realtime_market_provider_port import (
    RealtimeMarketProviderPort,
)
from libs.shared.src.dtos.market.ohlcv_dto import OhlcvDTO
from libs.shared.src.dtos.market.options_chain_dto import OptionsChainDTO


class RealtimeMarketYahooAdapter(RealtimeMarketProviderPort):
    """即時市場數據 - Yahoo Finance 實作"""

    def get_intraday_ohlcv(self, symbol: str, interval: str = "1m") -> list[OhlcvDTO]:
        """取得分鐘級數據

        Args:
            symbol: 股票代碼
            interval: 時間間隔 (1m, 5m, 15m, 30m, 1h)

        Returns:
            list[OhlcvDTO]: OHLCV 資料列表
        """
        # 處理台股代碼
        ticker_symbol = f"{symbol}.TW" if symbol.isdigit() else symbol

        try:
            ticker = yf.Ticker(ticker_symbol)

            # yfinance 分鐘數據最多回溯 7 天
            valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
            if interval not in valid_intervals:
                interval = "1m"

            # 1m 數據最多 7 天，其他最多 60 天
            period = "7d" if interval == "1m" else "30d"

            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return []

            result = []
            for idx, row in hist.iterrows():
                result.append(
                    {
                        "timestamp": idx.isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            return result

        except Exception:
            return []

    def get_options_chain(self, symbol: str) -> OptionsChainDTO:
        """取得選擇權鏈

        Args:
            symbol: 股票代碼 (美股)

        Returns:
            dict: {
                "expirations": [...],
                "calls": [...],
                "puts": [...],
                "underlying_price": float
            }
        """
        try:
            ticker = yf.Ticker(symbol)

            expirations = list(ticker.options)
            if not expirations:
                return {
                    "expirations": [],
                    "calls": [],
                    "puts": [],
                    "underlying_price": 0,
                }

            # 使用最近的到期日
            chain = ticker.option_chain(expirations[0])
            underlying_price = ticker.info.get("regularMarketPrice", 0)

            calls = []
            for _, row in chain.calls.iterrows():
                calls.append(
                    {
                        "strike": float(row["strike"]),
                        "lastPrice": float(row.get("lastPrice", 0) or 0),
                        "bid": float(row.get("bid", 0) or 0),
                        "ask": float(row.get("ask", 0) or 0),
                        "volume": int(row.get("volume", 0) or 0),
                        "openInterest": int(row.get("openInterest", 0) or 0),
                        "impliedVolatility": float(
                            row.get("impliedVolatility", 0) or 0
                        ),
                    }
                )

            puts = []
            for _, row in chain.puts.iterrows():
                puts.append(
                    {
                        "strike": float(row["strike"]),
                        "lastPrice": float(row.get("lastPrice", 0) or 0),
                        "bid": float(row.get("bid", 0) or 0),
                        "ask": float(row.get("ask", 0) or 0),
                        "volume": int(row.get("volume", 0) or 0),
                        "openInterest": int(row.get("openInterest", 0) or 0),
                        "impliedVolatility": float(
                            row.get("impliedVolatility", 0) or 0
                        ),
                    }
                )

            return {
                "expirations": expirations,
                "calls": calls,
                "puts": puts,
                "underlying_price": float(underlying_price),
            }

        except Exception:
            return {"expirations": [], "calls": [], "puts": [], "underlying_price": 0}
