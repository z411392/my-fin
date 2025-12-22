"""
DetectRegimeChangePort - Driving Port

實作者: DetectRegimeChangeCommand
"""

from typing import Protocol


class DetectRegimeChangePort(Protocol):
    """Driving Port for DetectRegimeChangeCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
