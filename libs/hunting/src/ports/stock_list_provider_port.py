"""股票清單提供者 Port"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class StockListProviderPort(Protocol):
    """股票清單提供者 Port

    用於取得可掃描的股票清單
    """

    def get_stock_list(self, exchange: str = "TSE") -> list[str]:
        """取得股票清單

        Args:
            exchange: 交易所 (TSE=上市, OTC=上櫃)

        Returns:
            list[str]: 股票代碼列表 (Yahoo Finance 格式)
        """
        ...

    def get_all_stocks(self, include_otc: bool = False) -> list[str]:
        """取得所有股票

        Args:
            include_otc: 是否包含上櫃

        Returns:
            list[str]: 股票代碼列表
        """
        ...
