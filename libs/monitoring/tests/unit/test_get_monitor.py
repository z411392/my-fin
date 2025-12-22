"""GetMonitorQuery 單元測試"""

from unittest.mock import MagicMock
import pytest
from libs.monitoring.src.application.queries.get_monitor import GetMonitorQuery


@pytest.fixture
def fake_adapters() -> dict:
    """建立所有必要的 fake adapters"""
    market_data = MagicMock()
    market_data.get_vix.return_value = 14.2
    market_data.get_daily_prices.return_value = [{"close": 100.0}] * 120

    vpin = MagicMock()
    vpin.calculate.return_value = {"vpin": 0.3, "level": "NORMAL"}

    gex = MagicMock()
    gex.calculate.return_value = {"gex": 0.0, "level": "NEUTRAL"}

    return {
        "market_data_adapter": market_data,
        "vpin_adapter": vpin,
        "gex_adapter": gex,
    }


class TestGetMonitorQuery:
    """測試 GetMonitorQuery"""

    def test_execute_returns_monitor_data(self, fake_adapters: dict) -> None:
        """應返回監控數據"""
        query = GetMonitorQuery(**fake_adapters)
        result = query.execute()

        assert "timestamp" in result
        assert "vix" in result
        assert "defcon" in result
        assert "vpin" in result
        assert "gex" in result
        assert "gli" in result
        assert "regime" in result

    def test_defcon_structure(self, fake_adapters: dict) -> None:
        """DEFCON 結構應正確"""
        query = GetMonitorQuery(**fake_adapters)
        result = query.execute()

        defcon = result["defcon"]
        assert "level" in defcon
        assert "emoji" in defcon
        assert "action" in defcon
        assert 1 <= defcon["level"] <= 5

    def test_vix_has_tier_and_kelly(self, fake_adapters: dict) -> None:
        """VIX 應包含 tier 和 kelly_factor"""
        query = GetMonitorQuery(**fake_adapters)
        result = query.execute()

        vix = result["vix"]
        assert "value" in vix
        assert "tier" in vix
        assert "kelly_factor" in vix
