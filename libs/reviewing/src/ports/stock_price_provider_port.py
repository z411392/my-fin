"""股票價格提供者 Port"""

from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class StockPriceProviderPort(Protocol):
    """股票價格提供者介面"""

    def get_current_price(self, symbol: str) -> Decimal:
        """取得股票當前價格

        Args:
            symbol: 股票代號 (台股: 2330.TW, 美股: AAPL)

        Returns:
            當前價格 (Decimal)
        """
        ...
