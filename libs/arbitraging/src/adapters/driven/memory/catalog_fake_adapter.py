"""Shioaji Catalog Fake Adapter

實作 CatalogProviderPort 和 USStockProviderPort，用於測試
模擬 Shioaji TDCC 商品檔 API 和 Wikipedia 美股清單
"""

from datetime import datetime

from libs.arbitraging.src.ports.catalog_provider_port import CatalogProviderPort
from libs.arbitraging.src.ports.us_stock_provider_port import USStockProviderPort
from libs.shared.src.dtos.catalog.catalog_dto import CatalogDTO
from libs.shared.src.dtos.catalog.stock_info_dto import StockInfoDTO
from libs.shared.src.dtos.catalog.stock_list_dto import GroupedStockList


class CatalogFakeAdapter(CatalogProviderPort, USStockProviderPort):
    """Shioaji Catalog Fake Adapter (同時實作台股和美股 Port)"""

    def __init__(self) -> None:
        self._tw_stocks: list[StockInfoDTO] = [
            {
                "code": "2330",
                "name": "台積電",
                "market": "TSE",
                "industry": "半導體",
                "currency": "TWD",
            },
            {
                "code": "2317",
                "name": "鴻海",
                "market": "TSE",
                "industry": "電子",
                "currency": "TWD",
            },
            {
                "code": "2454",
                "name": "聯發科",
                "market": "TSE",
                "industry": "半導體",
                "currency": "TWD",
            },
        ]
        self._us_stocks: GroupedStockList = {
            "russell_1000": [
                {"code": "AAPL", "sector": "SPY", "currency": "USD"},
                {"code": "MSFT", "sector": "SPY", "currency": "USD"},
            ],
            "sox": [
                {"code": "NVDA", "sector": "SMH", "currency": "USD"},
                {"code": "AMD", "sector": "SMH", "currency": "USD"},
            ],
        }

    def set_tw_stocks(self, stocks: list[StockInfoDTO]) -> None:
        """設置台股清單（測試用）"""
        self._tw_stocks = stocks

    def set_us_stocks(self, stocks: GroupedStockList) -> None:
        """設置美股清單（測試用）"""
        self._us_stocks = stocks

    def fetch_catalog(self) -> CatalogDTO:
        """從 Shioaji 撈取完整商品清單"""
        return {
            "tw_stocks": self._tw_stocks,
            "us_stocks": [],  # 由 fetch_us_stocks 處理
            "last_updated": datetime.now().isoformat(),
        }

    def fetch_us_stocks(self) -> GroupedStockList:
        """抓取美股清單 (Russell 1000 + SOX)"""
        return self._us_stocks
