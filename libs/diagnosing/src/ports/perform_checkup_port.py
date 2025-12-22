"""
PerformCheckupPort - Driving Port

實作者: PerformCheckupCommand
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.checkup_result_dto import CheckupResultDTO


class PerformCheckupPort(Protocol):
    """Driving Port for PerformCheckupCommand"""

    def execute(self, symbol: str) -> CheckupResultDTO:
        """執行主要操作"""
        ...
