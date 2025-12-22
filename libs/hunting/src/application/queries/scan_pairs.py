"""掃描配對交易 Query

實作 ScanPairsPort Driving Port
使用真實 Yahoo Finance 數據
"""

import logging

import numpy as np
import yfinance as yf

from libs.hunting.src.domain.services.pairs_detector import (
    scan_pairs,
    detect_pairs_opportunity,
)
from libs.hunting.src.ports.scan_pairs_port import ScanPairsPort
from libs.shared.src.dtos.hunting.pairs_scan_result_dto import PairsScanResultDTO


class ScanPairsQuery(ScanPairsPort):
    """掃描統計套利配對"""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    # 產業候選清單 (擴充版)
    SECTORS = {
        # ========== 台股 ==========
        "金融": {
            "TW": [
                "2881.TW",
                "2882.TW",
                "2891.TW",
                "2886.TW",
                "5880.TW",
                "2884.TW",
                "2880.TW",
                "5871.TW",
                "2883.TW",
                "2890.TW",
                "2885.TW",
                "2887.TW",
                "2889.TW",
                "2892.TW",
            ],
            "US": [
                "JPM",
                "BAC",
                "WFC",
                "GS",
                "MS",
                "C",
                "BLK",
                "SCHW",
                "AXP",
                "V",
                "MA",
            ],
        },
        "半導體": {
            "TW": [
                "2330.TW",
                "2454.TW",
                "3034.TW",
                "2379.TW",
                "3017.TW",
                "2303.TW",
                "3711.TW",
                "6415.TW",
                "2327.TW",
                "3037.TW",
                "2449.TW",
                "3443.TW",
                "2408.TW",
            ],
            "US": [
                "NVDA",
                "AMD",
                "INTC",
                "AVGO",
                "QCOM",
                "MU",
                "AMAT",
                "LRCX",
                "KLAC",
                "MRVL",
                "TXN",
                "ADI",
                "NXPI",
                "ON",
                "MCHP",
            ],
        },
        "電子零組件": {
            "TW": [
                "2317.TW",
                "2382.TW",
                "3231.TW",
                "2308.TW",
                "2474.TW",
                "3481.TW",
                "2345.TW",
                "2301.TW",
                "2313.TW",
                "2395.TW",
                "3008.TW",
                "2357.TW",
                "6669.TW",
                "3006.TW",
                "2376.TW",
            ],
        },
        "傳產": {
            "TW": [
                "1301.TW",
                "1303.TW",
                "1326.TW",
                "2002.TW",
                "2207.TW",
                "1402.TW",
                "2912.TW",
                "1216.TW",
                "1101.TW",
                "1102.TW",
                "2801.TW",
                "9910.TW",
                "2105.TW",
                "1504.TW",
                "2006.TW",
            ],
        },
        "塑化": {
            "TW": [
                "1301.TW",
                "1303.TW",
                "1326.TW",
                "6505.TW",
                "1304.TW",
                "1308.TW",
                "1309.TW",
                "1312.TW",
                "1314.TW",
                "1710.TW",
            ],
        },
        "航運": {
            "TW": [
                "2603.TW",
                "2609.TW",
                "2615.TW",
                "2618.TW",
                "2634.TW",
                "5608.TW",
                "2610.TW",
                "2606.TW",
                "2605.TW",
                "2637.TW",
            ],
        },
        "電信": {
            "TW": [
                "2412.TW",
                "3045.TW",
                "4904.TW",
                "2439.TW",
            ],
            "US": ["T", "VZ", "TMUS", "CMCSA", "CHTR"],
        },
        "生技": {
            "TW": [
                "4743.TW",
                "6446.TW",
                "4147.TW",
                "1760.TW",
                "4142.TW",
                "1795.TW",
                "4746.TW",
                "6472.TW",
                "4726.TW",
                "4736.TW",
            ],
            "US": ["JNJ", "PFE", "MRK", "ABBV", "BMY", "LLY", "AMGN", "GILD"],
        },
        "科技": {
            "US": [
                "AAPL",
                "MSFT",
                "GOOGL",
                "META",
                "AMZN",
                "NFLX",
                "CRM",
                "ORCL",
                "ADBE",
                "CSCO",
                "IBM",
                "NOW",
                "INTU",
                "SNOW",
                "PLTR",
                "DDOG",
            ],
        },
        "能源": {
            "US": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "VLO", "PSX", "OXY"],
        },
    }

    def execute(
        self,
        sector: str = "半導體",
        min_correlation: float = 0.5,  # 降低門檻
        market: str = "auto",
    ) -> PairsScanResultDTO:
        """掃描配對交易機會"""
        # 找到產業
        sector_key = None
        for key in self.SECTORS:
            if key in sector:
                sector_key = key
                break

        if not sector_key:
            sector_key = "半導體"

        sector_data = self.SECTORS[sector_key]

        # 決定市場
        if market == "auto":
            if "US" in sector.upper() or "美" in sector:
                market = "US"
            else:
                market = "TW"

        symbols = sector_data.get(
            market, sector_data.get("TW", sector_data.get("US", []))
        )

        if not symbols:
            return {
                "sector": sector_key,
                "market": market,
                "min_correlation": min_correlation,
                "pairs": [],
                "error": "無可用標的",
            }

        # 取得歷史數據
        valid_symbols, returns, prices = self._get_historical_data(symbols)

        if returns is None or len(returns) < 60:
            return {
                "sector": sector_key,
                "market": market,
                "min_correlation": min_correlation,
                "pairs": [],
                "error": "資料不足",
            }

        # 掃描配對 (使用有效的 symbols)
        results = scan_pairs(valid_symbols, returns, prices, min_correlation)

        pairs = []
        for pair in results[:5]:
            signal, _ = detect_pairs_opportunity(
                pair["spread_zscore"], pair["half_life"]
            )
            pairs.append(
                {
                    "symbol_a": pair["symbol_a"].replace(".TW", ""),
                    "symbol_b": pair["symbol_b"].replace(".TW", ""),
                    "correlation": round(pair["correlation"], 3),
                    "spread_zscore": round(pair["spread_zscore"], 2),
                    "half_life": round(pair["half_life"], 1),
                    "signal": signal,
                }
            )

        return {
            "sector": sector,
            "market": market,
            "min_correlation": min_correlation,
            "pairs": pairs,
        }

    def _get_historical_data(
        self, symbols: list[str], period: str = "6mo"
    ) -> tuple[list[str], np.ndarray | None, np.ndarray | None]:
        """取得多檔股票歷史數據

        Returns:
            tuple: (valid_symbols, returns, prices)
        """
        try:
            all_closes = []
            valid_symbols = []
            min_len = float("inf")

            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if hist is not None and len(hist) > 0:
                        closes = hist["Close"].values
                        all_closes.append(closes)
                        valid_symbols.append(symbol)
                        min_len = min(min_len, len(closes))
                except Exception:
                    continue  # 跳過取不到資料的股票

            if len(all_closes) < 2:
                return valid_symbols, None, None

            # 對齊長度
            prices = np.array([c[-int(min_len) :] for c in all_closes]).T
            returns = np.diff(np.log(prices), axis=0)

            return valid_symbols, returns, prices[1:]

        except Exception:
            return [], None, None
