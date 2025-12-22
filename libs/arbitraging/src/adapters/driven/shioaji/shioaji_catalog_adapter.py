from datetime import datetime
from typing import List
from injector import inject

from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
from libs.shared.src.dtos.catalog.catalog_dto import CatalogDTO
from libs.shared.src.dtos.catalog.stock_info_dto import StockInfoDTO
import logging
import time
from libs.arbitraging.src.ports.catalog_provider_port import CatalogProviderPort


class ShioajiCatalogAdapter(CatalogProviderPort):
    """Shioaji 商品檔適配器"""

    @inject
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_catalog(self) -> CatalogDTO:
        """從 Shioaji 撈取完整商品清單"""
        self.logger.info("開始撈取 Shioaji 商品檔...")

        tw_stocks: List[StockInfoDTO] = []
        us_stocks: List[StockInfoDTO] = []

        with ShioajiClient(simulation=True) as client:
            if not client.connected:
                self.logger.error("無法連線至 Shioaji，回傳空表")
                return {
                    "tw_stocks": [],
                    "us_stocks": [],
                    "last_updated": datetime.now().isoformat(),
                }

            api = client.api

            # 1. 確保合約已更新
            self.logger.info("Fetching contracts from Shioaji...")
            api.fetch_contracts(contract_download=True)

            # Wait for contracts to be fetched
            max_retries = 30
            for i in range(max_retries):
                # Status is an enum, we can check its name or value
                status = api.Contracts.status

                # Check if status name contains "Fetched" (e.g. FetchStatus.Fetched)
                if "Fetched" in str(status):
                    self.logger.info("Contracts fetched successfully.")
                    break
                time.sleep(1)
            else:
                self.logger.warning("Timeout waiting for contracts fetch")

            # 2. 遍歷所有股票合約
            # Shioaji contracts structure: api.Contracts.Stocks
            self.logger.info("Processing TW stocks...")
            for contract_group in api.Contracts.Stocks:
                # contract_group is StreamMultiContract (list of contracts)
                # We need to iterate over it
                for contract in contract_group:
                    exchange = getattr(contract, "exchange", "")
                    # 過濾條件: 上市 (TSE), 上櫃 (OTC), 興櫃 (OES/EMERGING)
                    market_map = {"TSE": "TSE", "OTC": "OTC", "OES": "EMERGING"}

                    if exchange in market_map:
                        code = getattr(contract, "code", "")
                        name = getattr(contract, "name", "")
                        tw_stocks.append(
                            {
                                "code": code,
                                "name": name,
                                "market": market_map[exchange],
                                "industry": getattr(contract, "industry_name", "")
                                or getattr(contract, "category", ""),
                                "currency": "TWD",
                            }
                        )

            # 3. 嘗試遍歷美股合約 (如果有權限)
            # 注意: Shioaji 美股通常在 ForeignStocks 或類似結構，視帳號權限而定
            # 嘗試讀取 ForeignStocks
            if hasattr(api.Contracts, "ForeignStocks"):
                self.logger.info("Processing US stocks...")
                for contract in api.Contracts.ForeignStocks:
                    # 假設 contract 有 exchange 為 NASDAQ, NYSE 等
                    # 需確認 Shioaji 外股合約結構
                    exchange = getattr(contract, "exchange", "US")
                    us_stocks.append(
                        {
                            "code": contract.code,
                            "name": contract.name,
                            "market": exchange,
                            "industry": getattr(contract, "industry_name", "")
                            or getattr(contract, "category", ""),
                            "currency": "USD",
                        }
                    )
            else:
                self.logger.warning("Shioaji API 未提供 ForeignStocks，跳過美股掃描")

        self.logger.info(
            f"撈取完成: 台股 {len(tw_stocks)} 檔, 美股 {len(us_stocks)} 檔"
        )

        return {
            "tw_stocks": tw_stocks,
            "us_stocks": us_stocks,
            "last_updated": datetime.now().isoformat(),
        }
