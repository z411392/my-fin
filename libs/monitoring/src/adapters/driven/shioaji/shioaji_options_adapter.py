"""Shioaji 選擇權 Adapter

實作 OptionsChainProviderPort，用於 GEX 計算的選擇權資料
"""

from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
from libs.shared.src.dtos.option_data_dto import OptionDataDTO


import logging
from libs.monitoring.src.ports.options_provider_port import OptionsProviderPort


class ShioajiOptionsAdapter(OptionsProviderPort):
    """Shioaji 選擇權資料查詢器"""

    def __init__(self, client: ShioajiClient) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._client = client

    def connect(self) -> bool:
        """連線"""
        return self._client.connect()

    def disconnect(self) -> None:
        """斷線"""
        self._client.disconnect()

    def get_spot_price(self, symbol: str) -> float:
        """取得現貨價格 (台指期近月)"""
        if not self._client.connected:
            if not self.connect():
                return 0.0

        try:
            api = self._client.api
            # 嘗試取得台指期近月價格
            futures = api.Contracts.Futures.TXF
            if futures:
                for contract in futures:
                    if hasattr(contract, "delivery_month"):
                        # 取第一個月份的快照
                        snapshot = api.snapshots([contract])
                        if snapshot:
                            return float(snapshot[0].close)
            return 0.0
        except Exception:
            return 0.0

    def get_options_chain(self, symbol: str = "TXO") -> list[OptionDataDTO]:
        """取得選擇權鏈"""
        if not self._client.connected:
            if not self.connect():
                return []

        try:
            api = self._client.api
            options = api.Contracts.Options

            if not hasattr(options, symbol):
                self._logger.info(f"找不到選擇權: {symbol}")
                return []

            option_contracts = getattr(options, symbol)
            result: list[OptionDataDTO] = []

            for contract in option_contracts:
                result.append(
                    OptionDataDTO(
                        code=contract.code,
                        symbol=contract.symbol,
                        name=getattr(contract, "name", ""),
                        delivery_month=getattr(contract, "delivery_month", ""),
                        strike_price=float(getattr(contract, "strike_price", 0)),
                        option_right=getattr(contract, "option_right", ""),
                    )
                )

            return result
        except Exception as e:
            self._logger.warning(f"取得選擇權鏈失敗: {e}")
            return []

    def get_near_month_options(self, symbol: str = "TXO") -> list[OptionDataDTO]:
        """取得近月選擇權合約"""
        all_options = self.get_options_chain(symbol)

        if not all_options:
            return []

        with_month = [o for o in all_options if o.get("delivery_month")]
        if not with_month:
            return all_options[:20]

        sorted_options = sorted(with_month, key=lambda x: x.get("delivery_month", ""))

        if sorted_options:
            near_month = sorted_options[0].get("delivery_month")
            return [o for o in sorted_options if o.get("delivery_month") == near_month]

        return []
