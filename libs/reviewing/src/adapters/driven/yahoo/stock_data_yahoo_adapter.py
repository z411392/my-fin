"""股票資料 Yahoo Finance Adapter

直接使用 yfinance SDK，實作 StockDataPort
"""

from datetime import date, timedelta
from decimal import Decimal
import time

import numpy as np
import yfinance as yf

from libs.hunting.src.domain.services.symbol_converter import to_yahoo_symbol
from libs.reviewing.src.ports.stock_data_provider_port import StockDataProviderPort


class StockDataYahooAdapter(StockDataProviderPort):
    """股票資料 Yahoo Finance Adapter"""

    def get_returns_matrix(
        self,
        symbols: list[str],
        days: int = 252,
    ) -> np.ndarray:
        """取得多標的報酬矩陣"""
        if not symbols:
            return np.array([])

        end_date = date.today()
        start_date = end_date - timedelta(days=int(days * 1.5))

        returns_list = []

        for symbol in symbols:
            yf_symbol = to_yahoo_symbol(symbol)
            try:
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date)

                if df.empty or len(df) < 20:
                    continue

                closes = df["Close"].values
                log_returns = np.diff(np.log(closes))

                if len(log_returns) > days:
                    log_returns = log_returns[-days:]

                returns_list.append(log_returns)

            except Exception:
                continue

        if not returns_list:
            return np.array([])

        min_len = min(len(r) for r in returns_list)
        aligned_returns = [r[-min_len:] for r in returns_list]

        return np.column_stack(aligned_returns)

    def get_average_daily_volume(
        self,
        symbol: str,
        days: int = 20,
    ) -> float:
        """取得平均日成交量"""
        end_date = date.today()
        start_date = end_date - timedelta(days=int(days * 1.5))
        yf_symbol = to_yahoo_symbol(symbol)

        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                return 0.0

            volumes = df["Volume"].tail(days).values
            return float(np.mean(volumes)) if len(volumes) > 0 else 0.0

        except Exception:
            return 0.0

    def get_current_price(self, symbol: str) -> Decimal:
        """取得現價"""
        yf_symbol = to_yahoo_symbol(str(symbol))

        for attempt in range(3):
            try:
                ticker = yf.Ticker(yf_symbol)
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
