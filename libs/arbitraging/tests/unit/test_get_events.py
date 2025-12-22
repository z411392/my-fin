"""GetEventsQuery 單元測試"""

from libs.arbitraging.src.adapters.driven.memory.event_calendar_fake_adapter import (
    EventCalendarFakeAdapter,
)


class TestGetEventsQuery:
    """事件日曆查詢測試"""

    def setup_method(self) -> None:
        self.calendar = EventCalendarFakeAdapter()

    def test_get_fomc_dates(self) -> None:
        """取得 FOMC 日期"""
        dates = self.calendar.get_fomc_dates(2025)
        assert len(dates) == 2
        assert "2025-01-29" in dates

    def test_get_witching_dates(self) -> None:
        """取得四巫日日期"""
        dates = self.calendar.get_witching_dates(2025)
        assert len(dates) == 2
        assert "2025-01-17" in dates

    def test_high_risk_event_count(self) -> None:
        """計算高風險事件數量"""
        fomc = self.calendar.get_fomc_dates(2025)
        witching = self.calendar.get_witching_dates(2025)
        high_risk_count = len(fomc) + len(witching)
        assert high_risk_count == 4

    def test_custom_fomc_dates(self) -> None:
        """設定自訂 FOMC 日期"""
        self.calendar.set_fomc_dates(["2025-06-18"])
        dates = self.calendar.get_fomc_dates(2025)
        assert len(dates) == 1
        assert "2025-06-18" in dates
