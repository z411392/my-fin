"""取得事件日曆 Query

實作 GetEventsPort Driving Port
使用 EconomicCalendarProviderPort 取得事件資料
"""

import logging

from injector import inject

from libs.arbitraging.src.ports.economic_calendar_provider_port import (
    EconomicCalendarProviderPort,
)
from libs.arbitraging.src.ports.get_events_port import GetEventsPort
from libs.shared.src.dtos.event.event_calendar_result_dto import (
    EventCalendarResultDTO,
)


class GetEventsQuery(GetEventsPort):
    """取得事件日曆"""

    HIGH_RISK_TYPES = {"FOMC", "FOMC_SEP", "WITCHING", "MSCI_SAIR"}
    MEDIUM_RISK_TYPES = {"CPI", "NFP", "MSCI_QIR", "CBC", "FUTURES_TW", "TSMC", "APPLE"}

    @inject
    def __init__(self, calendar: EconomicCalendarProviderPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._calendar = calendar

    def execute(
        self, days: int = 30, event_type: str | None = None
    ) -> EventCalendarResultDTO:
        """取得未來事件日曆

        Args:
            days: 查詢天數範圍
            event_type: 事件類型過濾

        Returns:
            EventCalendarResultDTO: 事件統計與列表
        """
        events = self._calendar.get_upcoming_events(days, event_type)

        high_risk_count = sum(1 for e in events if e.get("risk") == "HIGH")
        medium_risk_count = sum(1 for e in events if e.get("risk") == "MEDIUM")

        if high_risk_count > 0:
            suggested_action = "降槓桿 50%，禁止開新倉"
        elif medium_risk_count > 0:
            suggested_action = "降槓桿 30%，觀望"
        else:
            suggested_action = "正常操作"

        # 格式化事件
        formatted_events = []
        for e in events:
            formatted_events.append(
                {
                    "date": e["date"].strftime("%Y-%m-%d"),
                    "name": e["name"],
                    "type": e["type"],
                    "risk": e.get("risk", "LOW"),
                }
            )

        return {
            "days": days,
            "event_type": event_type,
            "events": formatted_events,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "suggested_action": suggested_action,
            "available_types": list(self._calendar.get_event_types().keys())
            if event_type is None
            else None,
        }
