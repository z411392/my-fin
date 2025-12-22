"""RunHourlyScanCommand 單元測試"""

from unittest.mock import MagicMock
import pytest
from libs.monitoring.src.application.commands.run_hourly_scan import (
    RunHourlyScanCommand,
)


@pytest.fixture
def fake_adapters() -> dict:
    """建立所有必要的 fake adapters"""
    market_data = MagicMock()
    market_data.get_vix.return_value = 14.2

    vpin = MagicMock()
    vpin.calculate.return_value = {"vpin": 0.3, "level": "NORMAL"}

    gex = MagicMock()
    gex.calculate.return_value = {"gex": 0.0, "level": "NEUTRAL"}

    return {
        "market_data_adapter": market_data,
        "vpin_adapter": vpin,
        "gex_adapter": gex,
    }


class TestRunHourlyScanCommand:
    """測試 RunHourlyScanCommand"""

    def test_execute_returns_scan_result(self, fake_adapters: dict) -> None:
        """應返回掃描結果"""
        command = RunHourlyScanCommand(**fake_adapters)
        result = command.execute()

        assert "timestamp" in result
        assert "alerts" in result

    def test_alerts_is_list(self, fake_adapters: dict) -> None:
        """警報應為列表"""
        command = RunHourlyScanCommand(**fake_adapters)
        result = command.execute()

        assert isinstance(result["alerts"], list)

    def test_scan_includes_vix(self, fake_adapters: dict) -> None:
        """掃描應包含 VIX"""
        command = RunHourlyScanCommand(**fake_adapters)
        result = command.execute()

        assert "vix" in result
