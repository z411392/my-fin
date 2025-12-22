"""股票清單 Fake Adapter

實作 StockListProviderPort，用於測試
"""

from libs.hunting.src.ports.stock_list_provider_port import StockListProviderPort


class StockListFakeAdapter(StockListProviderPort):
    """股票清單 Fake Adapter (用於測試)"""

    def __init__(self) -> None:
        self._stock_list: dict[str, list[str]] = {
            "TSE": ["2330.TW", "2317.TW", "2454.TW"],
            "OTC": ["3443.TWO", "6510.TWO"],
        }

    def set_stock_list(self, exchange: str, stocks: list[str]) -> None:
        """設置股票清單（測試用）"""
        self._stock_list[exchange] = stocks

    def get_stock_list(self, exchange: str = "TSE") -> list[str]:
        """取得股票清單"""
        return self._stock_list.get(exchange, [])

    def get_all_stocks(self, include_otc: bool = False) -> list[str]:
        """取得所有股票"""
        stocks = self._stock_list.get("TSE", []).copy()
        if include_otc:
            stocks.extend(self._stock_list.get("OTC", []))
        return stocks
