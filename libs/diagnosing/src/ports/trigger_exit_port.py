"""
TriggerExitPort - Driving Port

實作者: TriggerExitCommand
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.checkup_result_dto import TriggerExitResultDTO


class TriggerExitPort(Protocol):
    """Driving Port for TriggerExitCommand"""

    def execute(
        self, symbol: str, action: str = "REDUCE", reason: str = ""
    ) -> TriggerExitResultDTO:
        """執行主要操作"""
        ...
