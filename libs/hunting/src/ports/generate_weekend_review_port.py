"""
GenerateWeekendReviewPort - Driving Port

實作者: GenerateWeekendReviewCommand
"""

from typing import Protocol

from libs.shared.src.dtos.weekend_review_dto import WeekendReviewResultDTO


class GenerateWeekendReviewPort(Protocol):
    """Driving Port for GenerateWeekendReviewCommand"""

    def execute(
        self,
        watchlist: list[str] | None = None,
        scope: str = "default",
    ) -> WeekendReviewResultDTO:
        """執行週末總覽生成

        Args:
            watchlist: 觀察名單 (可選)
            scope: 掃描範圍 "default" 或 "full"

        Returns:
            WeekendReviewResultDTO: 週末總覽結果
        """
        ...
