"""
GetWeekendReviewPort - Driving Port

實作者: GetWeekendReviewQuery
"""

from typing import Protocol


class GetWeekendReviewPort(Protocol):
    """Driving Port for GetWeekendReviewQuery"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
