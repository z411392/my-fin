"""
GenerateHuntingListPort - Driving Port

實作者: GenerateHuntingListCommand
"""

from typing import Protocol


class GenerateHuntingListPort(Protocol):
    """Driving Port for GenerateHuntingListCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
