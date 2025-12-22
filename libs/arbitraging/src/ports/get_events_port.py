"""取得事件日曆 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.event.event_calendar_result_dto import (
    EventCalendarResultDTO,
)


class GetEventsPort(Protocol):
    """取得事件日曆

    CLI Entry: fin events
    """

    def execute(
        self, days: int = 30, event_type: str | None = None
    ) -> EventCalendarResultDTO:
        """
        取得未來事件日曆

        Args:
            days: 查看未來多少天
            event_type: 事件類型過濾 (fomc|cbc|msci|etf|futures|13f|tsmc|apple)

        Returns:
            EventCalendarResultDTO: 事件統計
        """
        ...
