"""同步商品目錄指令

從 Shioaji 和 Wikipedia 抓取完整商品清單，
依產業分群並生成合成指數 proxies，輸出至 data/catalog.json

注意：此指令已整合美股抓取邏輯，不再依賴 sync_us_index_command.py
"""

import json
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests
import yfinance as yf
from bs4 import BeautifulSoup
from injector import inject

from libs.arbitraging.src.ports.catalog_provider_port import CatalogProviderPort
from libs.arbitraging.src.ports.us_stock_provider_port import USStockProviderPort
from libs.arbitraging.src.ports.sync_catalog_port import SyncCatalogPort
from libs.shared.src.constants.industry_to_etf import INDUSTRY_TO_ETF
from libs.shared.src.constants.yfinance_settings import YFINANCE_DELAY_SECONDS
from libs.shared.src.dtos.catalog.raw_stock_dto import RawStockDTO
from libs.shared.src.dtos.catalog.stock_list_dto import (
    GroupedRawStockList,
    SectorProxiesMap,
    GroupedStockList,
)
from libs.shared.src.dtos.catalog.sync_result_dto import SyncResultDTO
import logging


# 需要生成 proxies 的產業（無專屬 ETF）
INDUSTRIES_NEED_PROXIES = {
    "01",  # 水泥
    "02",  # 食品
    "03",  # 塑膠
    "04",  # 紡織
    "05",  # 電機機械
    "06",  # 電器電纜
    "08",  # 玻璃陶瓷
    "09",  # 造紙
    "10",  # 鋼鐵
    "11",  # 橡膠
    "12",  # 汽車
    "14",  # 建材營造
    "15",  # 航運
    "16",  # 觀光
    "18",  # 貿易百貨
    "20",  # 其他
    "21",  # 化學
    "22",  # 生技醫療
    "23",  # 油電燃氣
    "32",  # 文化創意
    "33",  # 農業科技
    "34",  # 電子商務
    "35",  # 綠能環保
    "36",  # 數位雲端
    "37",  # 運動休閒
    "38",  # 居家生活
}

# 美股 GICS Sector → ETF 對照表
US_SECTOR_ETF_MAP: dict[str, str] = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Communication Services": "XLC",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
}

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


class SyncCatalogCommand(SyncCatalogPort):
    """同步商品目錄指令（含產業分群與 proxies 生成）"""

    # Wikipedia URLs
    RUSSELL_1000_URL = "https://en.wikipedia.org/wiki/Russell_1000_Index"
    SOX_URL = "https://en.wikipedia.org/wiki/PHLX_Semiconductor_Sector"

    @inject
    def __init__(
        self,
        catalog_adapter: CatalogProviderPort,
        us_stock_adapter: USStockProviderPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._catalog_adapter = catalog_adapter
        self._us_stock_adapter = us_stock_adapter
        self._catalog_path = Path("data/catalog.json")

    def execute(self, force: bool = False) -> SyncResultDTO:
        """執行同步

        Args:
            force: 是否忽略檔案存在強制更新

        Returns:
            SyncResultDTO: 執行結果摘要
        """
        if not force and self._catalog_path.exists():
            self._logger.info(f"Catalog {self._catalog_path} exists, checking age...")

        self._logger.info(f"Synchronizing catalog to {self._catalog_path}...")

        # 1. Fetch TW data from Shioaji
        self._logger.info("🔄 抓取台股清單 (Shioaji)...")
        raw_catalog = self._catalog_adapter.fetch_catalog()
        tw_stocks = raw_catalog.get("tw_stocks", [])

        if not tw_stocks:
            self._logger.warning("Fetched empty TW catalog. Aborting save.")
            return {"status": "failed", "message": "No TW data fetched from Shioaji"}

        # 2. Group TW stocks by ETF
        self._logger.info("🔄 依產業分群台股...")
        tw_grouped = self._group_tw_stocks(tw_stocks)

        # 3. Generate sector proxies with market cap sorting
        self._logger.info("🔄 生成產業代表股 (依市值排序)...")
        tw_proxies = self._generate_sector_proxies(tw_stocks)

        # 4. Fetch US data via injected adapter (arch.md R3)
        self._logger.info("🔄 抓取美股清單...")
        us_grouped = self._us_stock_adapter.fetch_us_stocks()

        # 5. Assemble final catalog
        catalog_data = {
            "tw": tw_grouped,
            "tw_sector_proxies": tw_proxies,
            "industry_to_etf": INDUSTRY_TO_ETF,
            "us": us_grouped,
            "us_sector_etf_map": US_SECTOR_ETF_MAP,
            "last_updated": datetime.now().isoformat(),
        }

        # 6. Save to file
        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, indent=2, ensure_ascii=False)

        # 7. Count stats
        tw_total = sum(len(stocks) for stocks in tw_grouped.values())
        us_total = len(us_grouped.get("russell_1000", [])) + len(
            us_grouped.get("sox", [])
        )

        self._logger.info(f"✅ Catalog saved: TW={tw_total}, US={us_total}")
        self._logger.info(f"   TW groups: {list(tw_grouped.keys())}")
        self._logger.info(f"   TW proxies: {len(tw_proxies)} industries")

        return {
            "status": "success",
            "tw_count": tw_total,
            "tw_groups": {k: len(v) for k, v in tw_grouped.items()},
            "tw_proxies_count": len(tw_proxies),
            "us_count": us_total,
            "path": str(self._catalog_path),
            "timestamp": catalog_data["last_updated"],
        }

    def _group_tw_stocks(self, tw_stocks: list[RawStockDTO]) -> GroupedRawStockList:
        """將台股依產業分群到 ETF"""
        groups: dict[str, list[RawStockDTO]] = {
            "0052": [],  # 電子
            "0055": [],  # 金融
            "0050": [],  # 其他
        }

        for stock in tw_stocks:
            # 只處理上市上櫃
            market = stock.get("market", "")
            if market not in ("TSE", "OTC"):
                continue

            industry = stock.get("industry", "").strip()
            etf = INDUSTRY_TO_ETF.get(industry, "0050")
            groups[etf].append(stock)

        return groups

    def _generate_sector_proxies(
        self, tw_stocks: list[RawStockDTO]
    ) -> SectorProxiesMap:
        """為無 ETF 產業生成代表股清單（依市值排序，取前 5 大）"""
        # 依產業分組（只看上市上櫃）
        by_industry: dict[str, list[RawStockDTO]] = defaultdict(list)

        for stock in tw_stocks:
            market = stock.get("market", "")
            if market not in ("TSE", "OTC"):
                continue

            industry = stock.get("industry", "").strip()
            if industry in INDUSTRIES_NEED_PROXIES:
                by_industry[industry].append(stock)

        # 每個產業取前 5 大（依市值排序）
        proxies: dict[str, list[str]] = {}

        for industry, stocks in by_industry.items():
            self._logger.info(f"   處理產業 {industry}: {len(stocks)} 檔...")

            # 只取前 20 檔候選，避免太慢
            candidates = stocks[:20]

            with_market_cap: list[tuple[str, float]] = []
            for stock in candidates:
                code = stock.get("code", "")
                try:
                    ticker = yf.Ticker(f"{code}.TW")
                    market_cap = ticker.info.get("marketCap", 0) or 0
                    with_market_cap.append((code, float(market_cap)))
                except Exception as e:
                    self._logger.debug(f"   無法取得 {code} 市值: {e}")
                    with_market_cap.append((code, 0.0))

                # Rate limit
                time.sleep(YFINANCE_DELAY_SECONDS)

            # 按市值排序
            sorted_stocks = sorted(with_market_cap, key=lambda x: x[1], reverse=True)
            proxies[industry] = [s[0] for s in sorted_stocks[:5]]
            self._logger.info(f"   產業 {industry} 龍頭: {proxies[industry]}")

        return proxies

    def _fetch_and_group_us_stocks(self) -> GroupedStockList:
        """抓取並組織美股資料"""
        # 1. 抓取 Russell 1000
        self._logger.info("   抓取 Russell 1000...")
        russell_1000 = self._fetch_from_wikipedia(self.RUSSELL_1000_URL)
        if len(russell_1000) < 500:
            self._logger.warning(
                f"Russell 1000 只抓到 {len(russell_1000)} 檔，使用備援..."
            )
            russell_1000 = self._get_russell_1000_fallback()
        self._logger.info(f"   ✅ Russell 1000: {len(russell_1000)} 檔")

        # 2. 抓取 SOX
        self._logger.info("   抓取 SOX...")
        sox = self._fetch_from_wikipedia(self.SOX_URL)
        if len(sox) < 10:
            self._logger.warning(f"SOX 只抓到 {len(sox)} 檔，使用備援...")
            sox = SOX_COMPONENTS_FALLBACK
        self._logger.info(f"   ✅ SOX: {len(sox)} 檔")

        # 3. 組織成新結構
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

    def _get_russell_1000_fallback(self) -> list[str]:
        """Russell 1000 備援清單"""
        return [
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
