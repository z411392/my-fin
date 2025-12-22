"""
RunDeepCheckupPort - Driving Port

實作者: RunDeepCheckupCommand
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.checkup_result_dto import DeepCheckupResultDTO


class RunDeepCheckupPort(Protocol):
    """Driving Port for RunDeepCheckupCommand"""

    def execute(self, symbol: str, send_email: bool = True) -> DeepCheckupResultDTO:
        """執行主要操作"""
        ...
