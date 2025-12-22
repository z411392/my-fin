"""經濟事件日曆提供者 Port

提供經濟事件日曆的查詢功能介面。
"""

from typing import Protocol

from libs.shared.src.dtos.catalog.event_type_map_dto import EventTypeMap
from libs.shared.src.dtos.event.economic_event_dto import EconomicEventDTO


class EconomicCalendarProviderPort(Protocol):
    """經濟事件日曆提供者介面"""

    def get_all_events(self, event_type: str | None = None) -> list[EconomicEventDTO]:
        """取得所有經濟事件

        Args:
            event_type: 可選，過濾特定事件類型

        Returns:
            list[EconomicEventDTO]: 事件列表
        """
        ...

    def get_upcoming_events(
        self, days: int = 30, event_type: str | None = None
    ) -> list[EconomicEventDTO]:
        """取得未來 N 天內的事件

        Args:
            days: 天數範圍
            event_type: 事件類型過濾

        Returns:
            list[EconomicEventDTO]: 事件列表
        """
        ...

    def get_event_types(self) -> EventTypeMap:
        """取得所有事件類型及其說明

        Returns:
            EventTypeMap: 事件類型 -> 說明
        """
        ...
