"""相關性計算器 Yahoo Adapter

使用 yfinance 獲取歷史價格並計算相關性矩陣
"""

from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from libs.monitoring.src.ports.correlation_provider_port import CorrelationProviderPort
from libs.shared.src.dtos.market.correlation_matrix_dto import CorrelationMatrixDTO


class CorrelationYahooAdapter(CorrelationProviderPort):
    """相關性計算器 - Yahoo Finance 實作"""

    def __init__(self, lookback_days: int = 60):
        self._lookback_days = lookback_days

    def calculate_matrix(self, symbols: list[str]) -> CorrelationMatrixDTO:
        """計算相關性矩陣

        Args:
            symbols: 股票代碼列表

        Returns:
            dict: {
                "symbols": [...],
                "matrix": [[...]],
                "avg_correlation": float,
                "max_pair": (str, str, float),
                "min_pair": (str, str, float)
            }
        """
        if len(symbols) < 2:
            return {
                "symbols": symbols,
                "matrix": [[1.0]] if symbols else [],
                "avg_correlation": 1.0,
            }

        # 獲取歷史價格
        end_date = date.today()
        start_date = end_date - timedelta(days=self._lookback_days + 10)

        prices = {}
        for symbol in symbols:
            try:
                # 處理台股代碼
                ticker_symbol = f"{symbol}.TW" if symbol.isdigit() else symbol
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(start=start_date, end=end_date)
                if not hist.empty:
                    prices[symbol] = hist["Close"]
            except Exception:
                continue

        if len(prices) < 2:
            return {
                "symbols": symbols,
                "matrix": [[1.0] * len(symbols) for _ in symbols],
                "avg_correlation": 1.0,
            }

        # 建立 DataFrame
        df = pd.DataFrame(prices).dropna()

        if len(df) < 10:
            return {
                "symbols": symbols,
                "matrix": [[1.0] * len(symbols) for _ in symbols],
                "avg_correlation": 1.0,
            }

        # 計算報酬率
        returns = df.pct_change().dropna()

        # 計算相關性矩陣
        corr_matrix = returns.corr()

        # 轉換為結果格式
        matrix = []
        valid_symbols = list(corr_matrix.columns)
        for sym in valid_symbols:
            row = [corr_matrix.loc[sym, s] for s in valid_symbols]
            matrix.append(row)

        # 找出最大/最小配對
        max_corr = -1.0
        min_corr = 1.0
        max_pair = (valid_symbols[0], valid_symbols[1], 0.0)
        min_pair = (valid_symbols[0], valid_symbols[1], 0.0)

        for i, sym1 in enumerate(valid_symbols):
            for j, sym2 in enumerate(valid_symbols):
                if i >= j:
                    continue
                corr = corr_matrix.loc[sym1, sym2]
                if corr > max_corr:
                    max_corr = corr
                    max_pair = (sym1, sym2, float(corr))
                if corr < min_corr:
                    min_corr = corr
                    min_pair = (sym1, sym2, float(corr))

        # 計算平均相關性 (排除對角線)
        n = len(valid_symbols)
        total_corr = sum(
            corr_matrix.loc[s1, s2]
            for i, s1 in enumerate(valid_symbols)
            for j, s2 in enumerate(valid_symbols)
            if i != j
        )
        avg_corr = total_corr / (n * (n - 1)) if n > 1 else 1.0

        return {
            "symbols": valid_symbols,
            "matrix": matrix,
            "avg_correlation": round(float(avg_corr), 4),
            "max_pair": max_pair,
            "min_pair": min_pair,
        }
