"""
RunHourlyScanPort - Driving Port

實作者: RunHourlyScanCommand
"""

from typing import Protocol


class RunHourlyScanPort(Protocol):
    """Driving Port for RunHourlyScanCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
