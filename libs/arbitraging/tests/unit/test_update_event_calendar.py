"""UpdateEventCalendarCommand 單元測試"""

from libs.arbitraging.src.application.commands.update_event_calendar import (
    UpdateEventCalendarCommand,
)


class TestUpdateEventCalendarCommand:
    """測試 UpdateEventCalendarCommand"""

    def test_execute_returns_events(self) -> None:
        """應返回事件列表"""
        command = UpdateEventCalendarCommand()
        result = command.execute(month=1, year=2025)

        assert "month" in result
        assert "year" in result
        assert "events_added" in result
        assert "events" in result
        assert result["month"] == 1
        assert result["year"] == 2025

    def test_generates_fomc_events(self) -> None:
        """應生成 FOMC 事件"""
        command = UpdateEventCalendarCommand()
        result = command.execute(month=3, year=2025)

        events = result["events"]
        fomc_events = [e for e in events if e["type"] == "FOMC"]
        assert len(fomc_events) > 0

    def test_generates_witching_events(self) -> None:
        """應在季末生成四巫日事件"""
        command = UpdateEventCalendarCommand()
        result = command.execute(month=3, year=2025)

        events = result["events"]
        witching_events = [e for e in events if e["type"] == "WITCHING"]
        assert len(witching_events) > 0

    def test_generates_msci_events(self) -> None:
        """應在 MSCI 調整月份生成事件"""
        command = UpdateEventCalendarCommand()
        result = command.execute(month=5, year=2025)

        events = result["events"]
        msci_events = [e for e in events if e["type"] == "MSCI"]
        assert len(msci_events) > 0
