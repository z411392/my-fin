"""事件日曆提供者 Port"""

from typing import Protocol


class EventCalendarProviderPort(Protocol):
    """事件日曆提供者介面"""

    def get_fomc_dates(self, year: int) -> list[str]:
        """取得 FOMC 會議日期"""
        ...

    def get_witching_dates(self, year: int) -> list[str]:
        """取得四巫日日期"""
        ...

    def get_earnings_dates(self, symbol: str) -> list[str]:
        """取得財報公布日期"""
        ...
