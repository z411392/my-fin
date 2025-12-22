"""Wikipedia 美股清單 Adapter

從 Wikipedia 抓取 Russell 1000 和 SOX 成分股
實作 USStockProviderPort
"""

import logging
import re

import requests
from bs4 import BeautifulSoup

from libs.arbitraging.src.ports.us_stock_provider_port import USStockProviderPort
from libs.shared.src.dtos.catalog.stock_list_dto import GroupedStockList


# SOX 半導體成分股（備援清單）
SOX_COMPONENTS_FALLBACK = [
    "AMD",
    "NVDA",
    "INTC",
    "AVGO",
    "QCOM",
    "TXN",
    "MU",
    "AMAT",
    "LRCX",
    "KLAC",
    "ADI",
    "NXPI",
    "MRVL",
    "ON",
    "MCHP",
    "SWKS",
    "QRVO",
    "MPWR",
    "ENTG",
    "WOLF",
    "ASML",
    "TSM",
]

# Russell 1000 備援清單（前 80 大）
RUSSELL_1000_FALLBACK = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "GOOG",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AMD",
    "AVGO",
    "QCOM",
    "TXN",
    "INTC",
    "MU",
    "MRVL",
    "LRCX",
    "AMAT",
    "KLAC",
    "ADI",
    "NXPI",
    "ON",
    "MCHP",
    "SWKS",
    "QRVO",
    "CRM",
    "ORCL",
    "ADBE",
    "NOW",
    "SNOW",
    "DDOG",
    "ZS",
    "PANW",
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "V",
    "MA",
    "AXP",
    "JNJ",
    "PFE",
    "ABBV",
    "MRK",
    "LLY",
    "UNH",
    "CVS",
    "TMO",
    "PG",
    "KO",
    "PEP",
    "COST",
    "WMT",
    "TGT",
    "HD",
    "LOW",
    "XOM",
    "CVX",
    "COP",
    "SLB",
    "OXY",
    "EOG",
    "MPC",
    "VLO",
    "CAT",
    "DE",
    "BA",
    "HON",
    "GE",
    "RTX",
    "LMT",
    "NOC",
    "DIS",
    "NFLX",
    "CMCSA",
    "T",
    "VZ",
    "TMUS",
    "CHTR",
]


class WikipediaUSStockAdapter(USStockProviderPort):
    """Wikipedia 美股清單 Adapter"""

    RUSSELL_1000_URL = "https://en.wikipedia.org/wiki/Russell_1000_Index"
    SOX_URL = "https://en.wikipedia.org/wiki/PHLX_Semiconductor_Sector"

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def fetch_us_stocks(self) -> GroupedStockList:
        """抓取美股清單"""
        # 1. 抓取 Russell 1000
        self._logger.info("   抓取 Russell 1000...")
        russell_1000 = self._fetch_from_wikipedia(self.RUSSELL_1000_URL)
        if len(russell_1000) < 500:
            self._logger.warning(
                f"Russell 1000 只抓到 {len(russell_1000)} 檔，使用備援..."
            )
            russell_1000 = RUSSELL_1000_FALLBACK
        self._logger.info(f"   ✅ Russell 1000: {len(russell_1000)} 檔")

        # 2. 抓取 SOX
        self._logger.info("   抓取 SOX...")
        sox = self._fetch_from_wikipedia(self.SOX_URL)
        if len(sox) < 10:
            self._logger.warning(f"SOX 只抓到 {len(sox)} 檔，使用備援...")
            sox = SOX_COMPONENTS_FALLBACK
        self._logger.info(f"   ✅ SOX: {len(sox)} 檔")

        # 3. 組織成結構
        russell_list = [
            {"code": code, "sector": "SPY", "currency": "USD"}
            for code in sorted(set(russell_1000))
        ]

        sox_list = [
            {"code": code, "sector": "SMH", "currency": "USD"}
            for code in sorted(set(sox))
        ]

        return {
            "russell_1000": russell_list,
            "sox": sox_list,
        }

    def _fetch_from_wikipedia(self, url: str) -> list[str]:
        """從 Wikipedia 抓取股票代碼"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            symbols = []

            tables = soup.find_all("table", class_="wikitable")
            for table in tables:
                header_row = table.find("tr")
                if not header_row:
                    continue

                headers_cells = header_row.find_all(["th", "td"])
                ticker_col_idx = -1

                for idx, cell in enumerate(headers_cells):
                    text = cell.get_text(strip=True).lower()
                    if "ticker" in text or "symbol" in text:
                        ticker_col_idx = idx
                        break

                if ticker_col_idx == -1:
                    continue

                rows = table.find_all("tr")
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    if len(cells) > ticker_col_idx:
                        cell = cells[ticker_col_idx]
                        text = cell.get_text(strip=True)
                        clean_text = re.sub(r"\[.*?\]", "", text).strip()

                        if "component" in clean_text.lower():
                            continue

                        if ":" in clean_text:
                            clean_text = clean_text.split(":")[-1].strip()

                        if (
                            clean_text
                            and 1 <= len(clean_text) <= 5
                            and clean_text.replace(".", "").isalpha()
                        ):
                            symbols.append(clean_text.upper())

            return list(set(symbols))

        except Exception as e:
            self._logger.warning(f"抓取失敗 ({url}): {e}")
            return []
