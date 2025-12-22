"""Fundamental Storage Port — Driven Port for StatementDog fundamental data storage"""

from typing import Protocol, runtime_checkable

from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)


@runtime_checkable
class FundamentalStoragePort(Protocol):
    """財報狗資料儲存埠

    儲存格式: data/fundamental/{symbol}.json
    無日期分層，只保留最新一份
    """

    def exists(self, symbol: str) -> bool:
        """檢查是否已存在

        Args:
            symbol: 股票代碼

        Returns:
            True if JSON file exists
        """
        ...

    def save(self, symbol: str, data: FundamentalSummaryDTO) -> None:
        """儲存資料

        Args:
            symbol: 股票代碼
            data: 要儲存的財報狗資料
        """
        ...

    def load(self, symbol: str) -> FundamentalSummaryDTO | None:
        """讀取資料

        Args:
            symbol: 股票代碼

        Returns:
            資料字典，若不存在則回傳 None
        """
        ...

    def list_all(self) -> list[str]:
        """列出所有已儲存的 symbol

        Returns:
            所有已儲存的 symbol 列表
        """
        ...
