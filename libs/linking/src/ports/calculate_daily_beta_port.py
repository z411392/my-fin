"""
CalculateDailyBetaPort - Driving Port

實作者: CalculateDailyBetaCommand
"""

from typing import Protocol


class CalculateDailyBetaPort(Protocol):
    """Driving Port for CalculateDailyBetaCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
