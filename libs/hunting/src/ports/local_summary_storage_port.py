"""Local Summary Storage Port — Driven Port for JSON file storage"""

from typing import Protocol, runtime_checkable

from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


@runtime_checkable
class LocalSummaryStoragePort(Protocol):
    """本地摘要儲存埠

    儲存格式: data/momentum/{date}/{symbol}.json
    """

    def exists(self, date: str, symbol: str) -> bool:
        """檢查是否已存在

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼

        Returns:
            True if JSON file exists
        """
        ...

    def save(self, date: str, symbol: str, data: ScanResultRowDTO) -> None:
        """儲存資料

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼
            data: 要儲存的資料
        """
        ...

    def load(self, date: str, symbol: str) -> ScanResultRowDTO | None:
        """讀取資料

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼

        Returns:
            資料字典，若不存在則回傳 None
        """
        ...

    def list_symbols(self, date: str) -> list[str]:
        """列出指定日期的所有 symbol

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            該日期已儲存的所有 symbol 列表
        """
        ...
