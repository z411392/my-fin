"""Export Daily Summary Port — Driving Port for CSV export"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExportDailySummaryPort(Protocol):
    """匯出每日摘要 Port"""

    def execute(self, date: str) -> str:
        """匯出指定日期的摘要至 CSV

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            產生的 CSV 檔案路徑
        """
        ...
