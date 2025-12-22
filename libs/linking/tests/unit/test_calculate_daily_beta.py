"""CalculateDailyBetaCommand 單元測試"""

from libs.linking.src.application.commands.calculate_daily_beta import (
    CalculateDailyBetaCommand,
)


class TestCalculateDailyBetaCommand:
    """測試 CalculateDailyBetaCommand"""

    def test_execute_returns_beta_data(self) -> None:
        """應返回 Beta 計算結果"""
        command = CalculateDailyBetaCommand()
        result = command.execute(us_symbol="NVDA", tw_symbol="3017", lookback=60)

        assert "us_symbol" in result
        assert "tw_symbol" in result
        assert "current_beta" in result
        assert "expected_tw_move" in result
        assert "lookback_days" in result
        assert "beta_history" in result

    def test_beta_in_reasonable_range(self) -> None:
        """Beta 應在合理範圍內"""
        command = CalculateDailyBetaCommand()
        result = command.execute(us_symbol="NVDA", tw_symbol="3017")

        beta = result["current_beta"]
        # Beta 通常在 0.2 到 2.0 之間
        assert -1 <= beta <= 3

    def test_beta_history_length(self) -> None:
        """Beta 歷史應包含最近值"""
        command = CalculateDailyBetaCommand()
        result = command.execute(us_symbol="NVDA", tw_symbol="3017")

        history = result["beta_history"]
        assert len(history) <= 5
