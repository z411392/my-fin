"""取得週度覆盤 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.weekly_review_dto import WeeklyReviewDTO


class GetWeeklyReviewPort(Protocol):
    """取得週度覆盤

    CLI Entry: fin review
    """

    def execute(self) -> WeeklyReviewDTO:
        """取得週度覆盤資料"""
        ...
