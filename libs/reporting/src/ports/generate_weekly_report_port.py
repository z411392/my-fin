"""生成週報 Port"""

from typing import Protocol

from libs.shared.src.dtos.reporting.report_result_dto import ReportResultDTO


class GenerateWeeklyReportPort(Protocol):
    """生成週報介面"""

    def execute(self, simulate: bool = False) -> ReportResultDTO:
        """執行生成週報

        Args:
            simulate: 是否使用模擬資料

        Returns:
            ReportResultDTO: 報告內容
        """
        ...
