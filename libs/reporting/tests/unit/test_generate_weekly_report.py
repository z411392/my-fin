"""GenerateWeeklyReportCommand Unit Tests"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def fake_adapters():
    """提供 Fake Adapters 給測試"""
    notification_gateway = MagicMock()
    notification_gateway.send_markdown_email.return_value = False

    portfolio_provider = MagicMock()
    portfolio_provider.connect.return_value = False
    portfolio_provider.get_positions.return_value = []

    return {
        "notification_gateway": notification_gateway,
        "portfolio_provider": portfolio_provider,
    }


class TestGenerateWeeklyReportCommand:
    """GenerateWeeklyReportCommand Tests"""

    def test_execute_returns_report_structure(self, fake_adapters):
        """測試執行返回正確的報告結構"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        assert "period" in result
        assert "performance" in result
        assert "skill" in result
        assert "crowding" in result
        assert "decision_quality" in result
        assert "thesis_validation" in result
        assert "strategy_health" in result
        assert "report_markdown" in result

    def test_performance_contains_required_fields(self, fake_adapters):
        """測試績效數據包含必要字段"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        performance = result["performance"]
        assert "mtd_return" in performance
        assert "ytd_return" in performance
        assert "sharpe_ratio" in performance
        assert "win_rate" in performance

    def test_skill_verdict(self, fake_adapters):
        """測試技能判定"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        skill = result["skill"]
        assert "dsr" in skill
        assert "psr" in skill
        assert "verdict" in skill
        assert skill["verdict"] in [
            "技能主導",
            "可能有技能",
            "運氣主導",
            "N/A (資料不足)",
        ]

    def test_strategy_health_contains_required_fields(self, fake_adapters):
        """測試策略健康度包含必要字段"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        health = result["strategy_health"]
        assert "dsr" in health
        assert "oos_sharpe" in health
        assert "pbo" in health
        assert "cpcv_mean" in health

    def test_thesis_validation_format(self, fake_adapters):
        """測試論點驗證格式"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        thesis = result["thesis_validation"]
        assert "total_theses" in thesis
        assert "valid_theses" in thesis
        assert "validity_rate" in thesis
        assert "details" in thesis

    def test_report_markdown_generated(self, fake_adapters):
        """測試 Markdown 報告生成"""
        from libs.reporting.src.application.commands.generate_weekly_report import (
            GenerateWeeklyReportCommand,
        )

        command = GenerateWeeklyReportCommand(
            notification_gateway=fake_adapters["notification_gateway"],
            portfolio_provider=fake_adapters["portfolio_provider"],
        )
        result = command.execute()

        markdown = result["report_markdown"]
        assert "週度覆盤" in markdown
        assert "績效" in markdown
        assert "技能判定" in markdown
        assert "策略健康度" in markdown
