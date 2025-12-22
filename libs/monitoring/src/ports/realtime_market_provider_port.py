"""
RealtimeMarketProviderPort - Driven Port

實作者: RealtimeMarketFakeAdapter
"""

from typing import Protocol

from libs.shared.src.dtos.market.ohlcv_dto import OhlcvDTO
from libs.shared.src.dtos.market.options_chain_dto import OptionsChainDTO


class RealtimeMarketProviderPort(Protocol):
    """Driven Port"""

    def get_intraday_ohlcv(self, symbol: str, interval: str) -> list[OhlcvDTO]:
        """取得分鐘級數據"""
        ...

    def get_options_chain(self, symbol: str) -> OptionsChainDTO:
        """取得選擇權鏈"""
        ...
