"""美股清單提供者 Port

定義美股清單資料來源介面
"""

from typing import Protocol

from libs.shared.src.dtos.catalog.stock_list_dto import GroupedStockList


class USStockProviderPort(Protocol):
    """美股清單提供者介面"""

    def fetch_us_stocks(self) -> GroupedStockList:
        """抓取美股清單 (Russell 1000 + SOX)

        Returns:
            GroupedStockList: 包含 russell_1000 和 sox 的清單
        """
        ...
