"""更新事件日曆 Command"""

import logging

from injector import inject
from datetime import date
from libs.arbitraging.src.ports.update_event_calendar_port import (
    UpdateEventCalendarPort,
)
from libs.shared.src.dtos.event.economic_event_dto import EconomicEventDTO
from libs.shared.src.dtos.event.event_command_result_dto import (
    EventCalendarUpdateResultDTO,
)


class UpdateEventCalendarCommand(UpdateEventCalendarPort):
    """更新事件日曆

    每月初執行，從外部來源同步事件資料
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self, month: int | None = None, year: int | None = None
    ) -> EventCalendarUpdateResultDTO:
        """執行更新事件日曆

        Args:
            month: 目標月份 (預設下個月)
            year: 目標年份 (預設今年)

        Returns:
            EventCalendarUpdateResultDTO: 新增/更新數量
        """

        today = date.today()
        target_month = month or (today.month % 12 + 1)
        target_year = year or (
            today.year if target_month > today.month else today.year + 1
        )

        # 預設事件列表 (實際應從 Fed/MSCI 等來源取得)
        events = self._generate_standard_events(target_year, target_month)

        return {
            "month": target_month,
            "year": target_year,
            "events_added": len(events),
            "events_updated": 0,
            "events": events,
        }

    def _generate_standard_events(
        self, year: int, month: int
    ) -> list[EconomicEventDTO]:
        """產生標準事件"""
        events = []

        # FOMC 會議 (每 6 週)
        if month in [1, 3, 5, 6, 7, 9, 11, 12]:
            events.append(
                {
                    "type": "FOMC",
                    "date": f"{year}-{month:02d}-15",
                    "impact": "HIGH",
                    "description": "FOMC 利率決策會議",
                }
            )

        # MSCI 調整 (2, 5, 8, 11 月)
        if month in [2, 5, 8, 11]:
            events.append(
                {
                    "type": "MSCI",
                    "date": f"{year}-{month:02d}-20",
                    "impact": "HIGH",
                    "description": "MSCI 季度調整",
                }
            )

        # 四巫日 (3, 6, 9, 12 月第三個週五)
        if month in [3, 6, 9, 12]:
            events.append(
                {
                    "type": "WITCHING",
                    "date": f"{year}-{month:02d}-20",
                    "impact": "HIGH",
                    "description": "四巫日",
                }
            )

        return events
