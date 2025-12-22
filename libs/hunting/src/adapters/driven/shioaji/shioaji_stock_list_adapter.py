"""Shioaji 股票清單 Adapter

實作 StockListProviderPort，用於取得可交易股票清單
"""

from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
import logging
from libs.hunting.src.ports.stock_list_provider_port import StockListProviderPort


class ShioajiStockListAdapter(StockListProviderPort):
    """Shioaji 股票清單 Adapter

    使用模擬模式取得可交易標的，比 TWSE API 更準確
    由 lifespan.py 注入 ShioajiClient
    """

    def __init__(self, client: ShioajiClient) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._client = client

    def connect(self) -> bool:
        """連線"""
        return self._client.connect()

    def disconnect(self) -> None:
        """斷線"""
        self._client.disconnect()

    def get_stock_list(self, exchange: str = "TSE") -> list[str]:
        """取得可交易股票清單"""
        if not self._client.connected:
            if not self.connect():
                return []

        try:
            api = self._client.api

            if exchange == "TSE":
                contracts = api.Contracts.Stocks.TSE
                suffix = ".TW"
            elif exchange == "OTC":
                contracts = api.Contracts.Stocks.OTC
                suffix = ".TWO"
            elif exchange == "NYSE":
                contracts = getattr(api.Contracts.Stocks, "NYSE", None)
                suffix = ""
            elif exchange == "NASDAQ":
                contracts = getattr(api.Contracts.Stocks, "NASDAQ", None)
                suffix = ""
            else:
                return []

            if not contracts:
                return []

            symbols = []
            for name in dir(contracts):
                if name.startswith("_"):
                    continue
                contract = getattr(contracts, name)
                if hasattr(contract, "code"):
                    code = contract.code
                    # 台股過濾 4 碼，美股則全收
                    if exchange in ("TSE", "OTC"):
                        if (
                            len(code) == 4
                            and code.isdigit()
                            and not code.startswith("00")
                        ):
                            symbols.append(f"{code}{suffix}")
                    else:
                        # 美股: 排除含有無法辨識字元的
                        if code.replace(".", "").isalpha():
                            symbols.append(code)

            return sorted(symbols)

        except Exception as e:
            self._logger.warning(f"取得股票清單失敗: {e}")
            return []

    def get_all_stocks(self, include_otc: bool = False) -> list[str]:
        """取得所有可交易股票"""
        stocks = self.get_stock_list("TSE")

        if include_otc:
            stocks.extend(self.get_stock_list("OTC"))

        return sorted(set(stocks))

    def get_us_tradable_stocks(self) -> list[str]:
        """取得 Shioaji 可交易美股清單"""
        nyse = self.get_stock_list("NYSE")
        nasdaq = self.get_stock_list("NASDAQ")
        return sorted(set(nyse + nasdaq))

    def get_us_stock_list(self) -> list[str]:
        """取得美股完整清單 (Russell 1000 + SOX)

        從 catalog.json 讀取，與 CatalogStockListAdapter 邏輯一致
        """
        import json
        from pathlib import Path

        data_path = Path(__file__).parents[6] / "data" / "catalog.json"
        try:
            with open(data_path, encoding="utf-8") as f:
                catalog = json.load(f)
        except FileNotFoundError:
            self._logger.warning(f"catalog.json 不存在: {data_path}")
            return []

        us_data = catalog.get("us", {})
        russell = us_data.get("russell_1000", [])
        sox = us_data.get("sox", [])

        russell_codes = [s["code"] if isinstance(s, dict) else s for s in russell]
        sox_codes = [s["code"] if isinstance(s, dict) else s for s in sox]

        # 合併去重
        all_codes = list(set(russell_codes + sox_codes))

        # 修正 Class A/B 股票符號
        all_codes = [s.replace(".", "-") for s in all_codes]

        return sorted(all_codes)
