import pytest
from unittest.mock import MagicMock

from libs.diagnosing.src.application.commands.run_deep_checkup import (
    RunDeepCheckupCommand,
)


class TestRunDeepCheckupCommand:
    @pytest.fixture
    def fake_deps(self):
        """提供 Fake Dependencies 給測試"""
        sd_client = MagicMock()
        sd_client.analyze.return_value = {"symbol": "2330"}
        sd_client.get_fundamental_summary.return_value = {
            "symbol": "2330",
            "is_valid": True,
            "revenue_momentum": {
                "short_term_yoy": 10.5,
                "long_term_yoy": 8.2,
                "current_yoy": 12.3,
                "is_accelerating": True,
            },
            "earnings_quality": {
                "cfo": 100000,
                "net_income": 80000,
                "cfo_ni_ratio": 1.25,
                "fcf_ttm": 50000,
                "is_quality": True,
            },
            "valuation_metrics": {
                "current_pe": 15.5,
                "pe_percentile_5": 10.0,
                "pe_percentile_25": 12.0,
                "pe_percentile_50": 15.0,
                "pe_percentile_75": 18.0,
                "pe_percentile_95": 22.0,
                "is_safe": True,
            },
            "f_score": {"score": 7, "details": {}},
            "raw_data": {},
        }

        momentum_query = MagicMock()
        momentum_query.evaluate_single_stock.return_value = {
            "symbol": "2330",
            "adjusted_r_momentum": 1.5,
            "sector": "Semiconductors",
        }
        momentum_query.execute.return_value = {"targets": []}

        pairs_query = MagicMock()
        pairs_query._get_historical_data.return_value = ([], None, None)

        supply_chain_query = MagicMock()
        supply_chain_query.execute.return_value = {
            "signal": "NO_DATA",
            "us_symbol": "NVDA",
            "tw_symbol": "2330",
        }

        notification_gateway = MagicMock()
        notification_gateway.send_markdown_email.return_value = True

        return {
            "sd_client": sd_client,
            "momentum_query": momentum_query,
            "pairs_query": pairs_query,
            "supply_chain_query": supply_chain_query,
            "notification_gateway": notification_gateway,
        }

    def test_execute_flow(self, fake_deps):
        command = RunDeepCheckupCommand(
            sd_client=fake_deps["sd_client"],
            momentum_query=fake_deps["momentum_query"],
            pairs_query=fake_deps["pairs_query"],
            supply_chain_query=fake_deps["supply_chain_query"],
            notification_gateway=fake_deps["notification_gateway"],
        )

        # Execute
        command.execute("2330")

        # Verify calls
        fake_deps["sd_client"].analyze.assert_called_once()
        fake_deps["momentum_query"].evaluate_single_stock.assert_called_with("2330")
        fake_deps["notification_gateway"].send_markdown_email.assert_called()
