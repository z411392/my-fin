"""事件日曆提供者 Fake Adapter"""

from libs.arbitraging.src.ports.event_calendar_provider_port import (
    EventCalendarProviderPort,
)


class EventCalendarFakeAdapter(EventCalendarProviderPort):
    """事件日曆 Mock 實作"""

    def __init__(self) -> None:
        self._fomc_dates: list[str] = ["2025-01-29", "2025-03-19"]
        self._witching_dates: list[str] = ["2025-01-17", "2025-03-21"]
        self._earnings_dates: dict[str, list[str]] = {}

    def get_fomc_dates(self, year: int) -> list[str]:
        return self._fomc_dates

    def get_witching_dates(self, year: int) -> list[str]:
        return self._witching_dates

    def get_earnings_dates(self, symbol: str) -> list[str]:
        return self._earnings_dates.get(symbol, [])

    # Setters for testing
    def set_fomc_dates(self, dates: list[str]) -> None:
        self._fomc_dates = dates

    def set_witching_dates(self, dates: list[str]) -> None:
        self._witching_dates = dates

    def set_earnings_dates(self, symbol: str, dates: list[str]) -> None:
        self._earnings_dates[symbol] = dates
