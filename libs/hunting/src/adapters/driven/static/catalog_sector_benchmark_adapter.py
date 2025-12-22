"""從 catalog.json 讀取產業 Benchmark 的 Adapter

實作 SectorBenchmarkProviderPort。
"""

import json
from functools import lru_cache
from pathlib import Path

from libs.hunting.src.ports.sector_benchmark_provider_port import (
    SectorBenchmarkProviderPort,
)
from libs.shared.src.dtos.catalog.industry_to_etf_map_dto import IndustryToEtfMap
from libs.shared.src.dtos.catalog.catalog_data_dto import CatalogDataDTO


# 產業代碼對照表
INDUSTRY_MAP: dict[str, str] = {
    "01": "水泥",
    "02": "食品",
    "03": "塑膠",
    "04": "紡織",
    "05": "電機機械",
    "06": "電器電纜",
    "08": "玻璃陶瓷",
    "09": "造紙",
    "10": "鋼鐵",
    "11": "橡膠",
    "12": "汽車",
    "14": "建材營造",
    "15": "航運",
    "16": "觀光",
    "17": "金融保險",
    "18": "貿易百貨",
    "20": "其他",
    "21": "化學",
    "22": "生技醫療",
    "23": "油電燃氣",
    "24": "半導體",
    "25": "電腦週邊",
    "26": "光電",
    "27": "通信網路",
    "28": "電子零組件",
    "29": "電子通路",
    "30": "資訊服務",
    "31": "其他電子",
    "32": "文化創意",
    "33": "農業科技",
    "34": "電子商務",
    "35": "綠能環保",
    "36": "數位雲端",
    "37": "運動休閒",
    "38": "居家生活",
}


class CatalogSectorBenchmarkAdapter(SectorBenchmarkProviderPort):
    """從 catalog.json 讀取產業 Benchmark"""

    def __init__(self) -> None:
        self.data_path = Path(__file__).parents[6] / "data" / "catalog.json"

    @lru_cache(maxsize=1)
    def _load_catalog_data(self) -> CatalogDataDTO:
        """從 JSON 載入商品目錄資料（帶快取）"""
        with open(self.data_path, encoding="utf-8") as f:
            return json.load(f)

    def get_sector_benchmark(self, symbol: str, market: str = "tw") -> str:
        """取得產業 benchmark"""
        if market.lower() == "tw" or market.lower().startswith("tw_"):
            return self._get_tw_sector_benchmark(symbol)
        else:
            return self._get_us_sector_benchmark(symbol)

    def _get_industry_to_etf(self) -> IndustryToEtfMap:
        """從 catalog.json 讀取產業→ETF 對照表"""
        catalog = self._load_catalog_data()
        return catalog.get("industry_to_etf", {})

    def _get_tw_sector_benchmark(self, symbol: str) -> str:
        """台股產業 benchmark"""
        industry = self.get_industry(symbol)
        if not industry:
            return "0050.TW"

        industry = industry.strip()
        industry_to_etf = self._get_industry_to_etf()

        etf = industry_to_etf.get(industry)
        if etf:
            return f"{etf}.TW"

        return f"synthetic:{industry}"

    def _get_us_sector_benchmark(self, symbol: str) -> str:
        """美股產業 benchmark"""
        catalog = self._load_catalog_data()
        us_data = catalog.get("us", {})

        for index_name in ["russell_1000", "sox"]:
            stocks = us_data.get(index_name, [])
            for stock in stocks:
                if isinstance(stock, dict) and stock.get("code") == symbol:
                    sector = stock.get("sector", "SPY")
                    return sector

        return "SPY"

    def get_sector_proxies(self, industry: str) -> list[str]:
        """取得產業代表股清單"""
        catalog = self._load_catalog_data()
        proxies = catalog.get("tw_sector_proxies", {})
        return proxies.get(industry, [])

    def get_industry(self, symbol: str) -> str | None:
        """取得股票的產業代碼"""
        code = symbol.replace(".TW", "")
        catalog = self._load_catalog_data()
        tw_data = catalog.get("tw", {})

        # 新結構（分群）
        if isinstance(tw_data, dict) and "0050" in tw_data:
            for _etf_key, stocks in tw_data.items():
                for stock in stocks:
                    if stock.get("code") == code:
                        return stock.get("industry")
        else:
            # 向後相容
            for stock in catalog.get("tw_stocks", []):
                if stock.get("code") == code:
                    return stock.get("industry")

        return None

    def get_industry_name(self, symbol: str) -> str:
        """取得股票的產業名稱"""
        industry_code = self.get_industry(symbol)
        if industry_code:
            return INDUSTRY_MAP.get(industry_code.strip(), "未知")
        return "未知"
