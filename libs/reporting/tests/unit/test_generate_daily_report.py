"""GenerateDailyReportCommand Unit Tests"""

import sys
import pytest
from unittest.mock import patch
from libs.reporting.src.application.commands.generate_daily_report import (
    GenerateDailyReportCommand,
)
from libs.shared.src.enums.defcon_level import DefconLevel
from libs.shared.src.enums.vix_tier import VixTier


# Python 3.13 + Shioaji C extension 會導致 Segmentation fault
# 在 CI 環境（非 macOS arm64）可能正常運作
pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason="Python 3.13 + Shioaji C extension causes Segmentation fault on macOS arm64",
)


class TestGenerateDailyReportCommand:
    """GenerateDailyReportCommand Tests"""

    @pytest.fixture
    def stub_dependencies(self):
        """Stub 所有外部依賴"""
        with (
            patch(
                "libs.monitoring.src.adapters.driven.yahoo.market_data_adapter.YahooMarketDataAdapter"
            ) as stub_yahoo,
            patch(
                "libs.reviewing.src.adapters.driven.shioaji.shioaji_portfolio_adapter.ShioajiPortfolioAdapter"
            ) as stub_shioaji,
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.ScanResidualMomentumQuery"
            ) as stub_momentum,
            patch(
                "libs.hunting.src.application.queries.scan_pairs.ScanPairsQuery"
            ) as stub_pairs,
            patch(
                "libs.linking.src.application.queries.get_supply_chain_link.GetSupplyChainLinkQuery"
            ) as stub_supply,
            patch(
                "libs.calculators.src.defcon_calculator.calculate_defcon_level"
            ) as stub_calc_defcon,
            patch(
                "libs.calculators.src.vix_tier_calculator.calculate_vix_tier"
            ) as stub_calc_vix,
            patch(
                "libs.reporting.src.application.commands.generate_daily_report.GenerateDailyReportCommand._calculate_hmm_state_and_prob"
            ) as stub_hmm,
            patch(
                "libs.reporting.src.application.commands.generate_daily_report.GenerateDailyReportCommand._calculate_gli_z"
            ) as stub_gli,
        ):
            # Setup Defaults
            stub_yahoo_instance = stub_yahoo.return_value
            stub_yahoo_instance.get_vix.return_value = 15.0

            stub_shioaji_instance = stub_shioaji.return_value
            stub_shioaji_instance.connect.return_value = True
            stub_shioaji_instance.get_position_with_stop_loss.return_value = [
                {
                    "symbol": "2330",
                    "current_price": 1000,
                    "cost": 800,
                    "stop_loss": 750,
                    "status": "✅",
                    "buffer_pct": 20.0,
                }
            ]

            stub_momentum_instance = stub_momentum.return_value
            stub_momentum_instance.execute.return_value = {
                "scanned": 100,
                "targets": [{"symbol": "2330", "momentum": 2.5}],
                "top_targets": [{"symbol": "2330", "momentum": 2.5}],
                "bottom_targets": [{"symbol": "2317", "momentum": -2.0}],
            }

            stub_pairs_instance = stub_pairs.return_value
            stub_pairs_instance.execute.return_value = {"pairs": []}

            stub_supply_instance = stub_supply.return_value
            stub_supply_instance.execute.return_value = {"signal": "NONE"}

            stub_calc_defcon.return_value = (DefconLevel.DEFCON_5, "🟢", "全自動")
            stub_calc_vix.return_value = (VixTier.TIER_1, "🟢", "正常")

            stub_hmm.return_value = (0, 0.6)  # Bull
            stub_gli.return_value = 1.0

            yield {
                "yahoo": stub_yahoo,
                "shioaji": stub_shioaji,
                "momentum": stub_momentum,
                "pairs": stub_pairs,
                "defcon": stub_calc_defcon,
            }

    def test_execute_returns_report_structure(self, stub_dependencies):
        """測試執行返回正確的報告結構 (含週報合併功能)"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        # 原有欄位
        assert "date" in result
        assert "weather" in result
        assert "portfolio" in result
        assert "events" in result
        assert "entry_checklist" in result
        assert "todos" in result
        assert "report_markdown" in result

        # 從週報合併的欄位
        assert "advisors" in result
        # hunting_list 已移除，改用 Google Sheets 連結
        assert "pairs" in result
        assert "supply_chain" in result
        assert "halt" in result

    def test_weather_contains_required_fields(self, stub_dependencies):
        """測試天候數據包含必要字段"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        weather = result["weather"]
        assert "vix" in weather
        assert "vix_tier" in weather
        assert "defcon_level" in weather
        assert "overall_signal" in weather
        assert weather["overall_signal"] in ["🟢", "🟡", "🔴", "🔴 (Data Error)"]

    def test_four_advisors_consensus(self, stub_dependencies):
        """測試四顧問診斷 (從週報合併)"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        advisors = result["advisors"]
        assert "engineer" in advisors
        assert "biologist" in advisors
        assert "psychologist" in advisors
        assert "strategist" in advisors
        assert "consensus" in advisors
        assert "allocation" in advisors

    def test_portfolio_health_calculation(self, stub_dependencies):
        """測試持倉健康度計算"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        portfolio = result["portfolio"]
        assert "positions" in portfolio
        assert "healthy_count" in portfolio
        assert "total_count" in portfolio

    def test_entry_checklist_decision(self, stub_dependencies):
        """測試進場決策檢表"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        checklist = result["entry_checklist"]
        assert "checks" in checklist
        assert "passed_count" in checklist
        assert "decision" in checklist
        assert (
            "🟢" in checklist["decision"]
            or "🟡" in checklist["decision"]
            or "🔴" in checklist["decision"]
        )

    def test_halt_check_default_passed(self, stub_dependencies):
        """測試 HALT 自檢預設通過 (從週報合併)"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        halt = result["halt"]
        assert halt["passed"] is True
        assert halt["hungry"] is False
        assert halt["angry"] is False
        assert halt["lonely"] is False
        assert halt["tired"] is False

    def test_events_format(self, stub_dependencies):
        """測試事件格式"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        events = result["events"]
        assert isinstance(events, list)
        if events:
            event = events[0]
            assert "date" in event
            assert "event" in event
            assert "risk_level" in event

    def test_report_markdown_generated(self, stub_dependencies):
        """測試 Markdown 報告生成 (含週報內容)"""
        command = GenerateDailyReportCommand()
        result = command.execute(simulate=True)

        markdown = result["report_markdown"]
        assert "每日簡報" in markdown
        assert "天候燈號" in markdown
        assert "四顧問診斷" in markdown
        assert "持倉健康" in markdown
        assert "配對交易" in markdown
        # 殘差動能改用 Google Sheets 連結
        assert "殘差動能掃描結果" in markdown
        assert "Google Sheets" in markdown
        assert "HALT 自檢" in markdown
