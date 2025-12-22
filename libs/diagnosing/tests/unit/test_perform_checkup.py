"""PerformCheckupCommand 單元測試"""

from unittest.mock import MagicMock
from libs.diagnosing.src.ports.financial_data_provider_port import (
    FinancialDataProviderPort,
)

from libs.diagnosing.src.application.commands.perform_checkup import (
    PerformCheckupCommand,
)


class TestPerformCheckupCommand:
    """測試 PerformCheckupCommand"""

    def setup_method(self) -> None:
        """設置測試"""
        self.mock_provider = MagicMock(spec=FinancialDataProviderPort)

        # Mock daily prices for symbol and SPY
        mock_prices = []
        for i in range(50):
            mock_prices.append(
                {
                    "date": f"2023-01-{i + 1:02d}"
                    if i < 30
                    else f"2023-02-{i - 29:02d}",
                    "close": 100.0 + i * 0.1,
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "volume": 1000,
                }
            )

        self.mock_provider.get_daily_prices.return_value = mock_prices

        self.command = PerformCheckupCommand(self.mock_provider)

    def test_execute_returns_checkup_result(self) -> None:
        """應返回健檢結果"""
        result = self.command.execute(symbol="2330")

        assert "symbol" in result
        assert "diagnosis" in result
        assert result["symbol"] == "2330"

    def test_diagnosis_has_verdict(self) -> None:
        """診斷應包含裁決"""
        result = self.command.execute(symbol="2330")

        diagnosis = result["diagnosis"]
        assert "verdict" in diagnosis

    def test_diagnosis_has_dimensions(self) -> None:
        """診斷應包含各維度評分"""
        result = self.command.execute(symbol="2330")

        diagnosis = result["diagnosis"]
        assert "dimensions" in diagnosis

    def test_dimensions_has_five_items(self) -> None:
        """應有 5 個維度評估"""
        result = self.command.execute(symbol="2330")
        dimensions = result["diagnosis"]["dimensions"]

        assert len(dimensions) == 5

    def test_each_dimension_has_required_fields(self) -> None:
        """每個維度應有必要欄位"""
        result = self.command.execute(symbol="2330")
        dimensions = result["diagnosis"]["dimensions"]

        for dim in dimensions:
            assert "name" in dim
            assert "passed" in dim
            assert "value" in dim

    def test_verdict_is_valid(self) -> None:
        """verdict 應為有效值"""
        result = self.command.execute(symbol="2330")
        verdict = result["diagnosis"]["verdict"]

        valid_verdicts = ["KEEP", "HOLD", "REDUCE", "SELL"]
        assert verdict in valid_verdicts

    def test_score_matches_passed_count(self) -> None:
        """score 應等於通過的維度數"""
        result = self.command.execute(symbol="2330")
        dimensions = result["diagnosis"]["dimensions"]
        score = result["diagnosis"]["score"]

        passed_count = sum(1 for d in dimensions if d["passed"])
        assert score == passed_count

    def test_same_symbol_produces_same_result(self) -> None:
        """相同股票應產生相同結果 (確定性隨機)"""
        result1 = self.command.execute(symbol="2330")
        result2 = self.command.execute(symbol="2330")

        assert result1["diagnosis"]["verdict"] == result2["diagnosis"]["verdict"]

    def test_different_symbols_may_differ(self) -> None:
        """不同股票應可能產生不同結果"""
        result1 = self.command.execute(symbol="2330")
        result2 = self.command.execute(symbol="2317")

        # 格式相同
        assert "verdict" in result1["diagnosis"]
        assert "verdict" in result2["diagnosis"]
