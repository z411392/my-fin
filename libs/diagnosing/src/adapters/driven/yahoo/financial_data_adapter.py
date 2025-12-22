"""Stock Checkup - Yahoo Finance Financial Data Adapter"""

import time
from datetime import date, timedelta

import yfinance as yf
from libs.diagnosing.src.ports.financial_data_provider_port import (
    FinancialDataProviderPort,
)
from libs.shared.src.dtos.analysis.earnings_dto import EarningsDTO
from libs.shared.src.dtos.analysis.financial_info_dto import (
    FinancialInfoDTO,
    AnalystRatingsDTO,
)
from libs.shared.src.dtos.market.ohlcv_dto import DailyOhlcvDTO


class YahooFinancialDataAdapter(FinancialDataProviderPort):
    """財務數據 Adapter (使用 Yahoo Finance)

    取得個股基本面：股價、本益比、毛利率、ROE 等
    """

    def get_financial_info(self, symbol: str) -> FinancialInfoDTO:
        """取得個股財務資訊

        Returns:
            dict: {
                "symbol": 股票代號,
                "name": 公司名稱,
                "price": 現價,
                "pe_ratio": 本益比,
                "pb_ratio": 股價淨值比,
                "dividend_yield": 殖利率 (%),
                "market_cap": 市值,
                "revenue_growth": 營收成長率 (%),
                "gross_margin": 毛利率 (%),
                "operating_margin": 營業利益率 (%),
                "roe": 股東權益報酬率 (%),
                "debt_to_equity": 負債權益比,
                "current_ratio": 流動比率,
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice", 0),
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE") or 0,
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": (info.get("dividendYield") or 0) * 100,
                "market_cap": info.get("marketCap", 0),
                "revenue_growth": (info.get("revenueGrowth") or 0) * 100,
                "gross_margin": (info.get("grossMargins") or 0) * 100,
                "operating_margin": (info.get("operatingMargins") or 0) * 100,
                "roe": (info.get("returnOnEquity") or 0) * 100,
                "debt_to_equity": info.get("debtToEquity", 0),
                "current_ratio": info.get("currentRatio", 0),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
            }

    def get_earnings_history(self, symbol: str) -> list[EarningsDTO]:
        """取得歷史財報資料"""
        try:
            ticker = yf.Ticker(symbol)
            earnings = ticker.earnings_history

            if earnings is None or earnings.empty:
                return []

            result = []
            for idx, row in earnings.iterrows():
                result.append(
                    {
                        "date": idx.strftime("%Y-%m-%d")
                        if hasattr(idx, "strftime")
                        else str(idx),
                        "eps_estimate": float(row.get("epsEstimate", 0)),
                        "eps_actual": float(row.get("epsActual", 0)),
                        "surprise": float(row.get("surprise", 0)),
                        "surprise_pct": float(row.get("surprisePercent", 0)) * 100,
                    }
                )
            return result

        except Exception:
            return []

    def get_analyst_ratings(self, symbol: str) -> AnalystRatingsDTO:
        """取得分析師評等"""
        try:
            ticker = yf.Ticker(symbol)
            recs = ticker.recommendations

            if recs is None or recs.empty:
                return {
                    "buy": 0,
                    "hold": 0,
                    "sell": 0,
                    "strong_buy": 0,
                    "strong_sell": 0,
                }

            latest = recs.tail(30)  # 最近 30 筆評等
            counts = latest["To Grade"].value_counts().to_dict()

            return {
                "strong_buy": counts.get("Strong Buy", 0) + counts.get("Outperform", 0),
                "buy": counts.get("Buy", 0) + counts.get("Overweight", 0),
                "hold": counts.get("Hold", 0)
                + counts.get("Neutral", 0)
                + counts.get("Equal-Weight", 0),
                "sell": counts.get("Sell", 0) + counts.get("Underweight", 0),
                "strong_sell": counts.get("Strong Sell", 0)
                + counts.get("Underperform", 0),
            }

        except Exception:
            return {"buy": 0, "hold": 0, "sell": 0, "strong_buy": 0, "strong_sell": 0}

    def get_daily_prices(self, symbol: str, days: int = 252) -> list[DailyOhlcvDTO]:
        """取得日級價格資料"""
        end_date = date.today()
        # 多抓一點 buffer 確保資料足夠
        start_date = end_date - timedelta(days=days + 60)

        try:
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
            # 只回傳最後 days 筆? 或是回傳範圍內的?
            # 這裡回傳抓到的全部，呼叫端自己切
            return result
        except Exception:
            return []

    def get_current_price(self, symbol: str) -> float:
        """取得現價"""
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
                return 0.0
            except Exception:
                if attempt < 2:
                    time.sleep(1)
                    continue
                return 0.0
        return 0.0
