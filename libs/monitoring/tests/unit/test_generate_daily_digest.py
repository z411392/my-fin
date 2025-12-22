"""GenerateDailyDigestCommand 單元測試"""

import os
from unittest import mock
from unittest.mock import MagicMock
from libs.monitoring.src.application.commands.generate_daily_digest import (
    GenerateDailyDigestCommand,
)
import pytest


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

    fred = MagicMock()
    fred.get_gli_z_score.return_value = 0.8

    portfolio = MagicMock()
    portfolio.get_position_with_stop_loss.return_value = []

    notification = MagicMock()
    notification._send_email.return_value = False

    return {
        "market_data_adapter": market_data,
        "vpin_adapter": vpin,
        "gex_adapter": gex,
        "fred_adapter": fred,
        "portfolio_adapter": portfolio,
        "notification_gateway": notification,
    }


@mock.patch.dict(os.environ, {"SHIOAJI_API_KEY": ""})
class TestGenerateDailyDigestCommand:
    """測試 GenerateDailyDigestCommand"""

    def test_execute_returns_digest_data(self, fake_adapters: dict) -> None:
        """應返回完整的簡報數據"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(simulate=True)

        assert "date" in result
        assert "weather" in result
        assert "portfolio" in result
        assert "events" in result
        assert "entry_checklist" in result
        assert "todos" in result
        assert "report_markdown" in result

    def test_weather_has_required_fields(self, fake_adapters: dict) -> None:
        """天候應包含必要欄位"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(simulate=True)

        weather = result["weather"]
        assert "vix" in weather
        assert "defcon_level" in weather
        assert "overall_signal" in weather
        assert "overall_action" in weather

    def test_portfolio_health_calculation(self, fake_adapters: dict) -> None:
        """持倉健康度計算應正確"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(simulate=True)

        portfolio = result["portfolio"]
        assert "positions" in portfolio
        assert "healthy_count" in portfolio
        assert "total_count" in portfolio
        assert portfolio["healthy_count"] <= portfolio["total_count"]

    def test_entry_checklist_decision(self, fake_adapters: dict) -> None:
        """進場決策檢表應有決策"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(simulate=True)

        checklist = result["entry_checklist"]
        assert "checks" in checklist
        assert "passed_count" in checklist
        assert "decision" in checklist
        assert checklist["passed_count"] <= checklist["total_count"]

    def test_report_markdown_generated(self, fake_adapters: dict) -> None:
        """應生成 Markdown 報告"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(simulate=True)

        report = result["report_markdown"]
        assert "每日簡報" in report
        assert "天候燈號" in report
        assert "持倉健康" in report

    def test_email_not_sent_by_default(self, fake_adapters: dict) -> None:
        """預設不發送 email"""
        command = GenerateDailyDigestCommand(**fake_adapters)
        result = command.execute(send_email=False, simulate=True)

        assert result["email_sent"] is False
