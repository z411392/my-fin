"""Get Stock Row Port

Driving Port — 取得單一股票資料
"""

from typing import Protocol

from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


class GetStockRowPort(Protocol):
    """取得單一股票資料的介面"""

    async def execute(self, date: str, symbol: str) -> ScanResultRowDTO | None:
        """取得指定日期的單一股票資料

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼

        Returns:
            股票資料，若找不到則回傳 None
        """
        ...
