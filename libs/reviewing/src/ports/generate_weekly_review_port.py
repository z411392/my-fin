"""
GenerateWeeklyReviewPort - Driving Port

實作者: GenerateWeeklyReviewCommand
"""

from typing import Protocol


class GenerateWeeklyReviewPort(Protocol):
    """Driving Port for GenerateWeeklyReviewCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
