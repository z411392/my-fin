"""TriggerExitCommand 單元測試"""

from libs.diagnosing.src.application.commands.trigger_exit import TriggerExitCommand


class TestTriggerExitCommand:
    """測試 TriggerExitCommand"""

    def test_execute_reduce_action(self) -> None:
        """REDUCE 動作應減碼一半"""
        command = TriggerExitCommand()
        result = command.execute(symbol="2330", action="REDUCE", reason="論點失效")

        assert result["symbol"] == "2330"
        assert result["action"] == "REDUCE"
        assert result["target_position_pct"] == 0.5
        assert result["urgency"] == "MEDIUM"
        assert "論點失效" in result["reason"]

    def test_execute_sell_action(self) -> None:
        """SELL 動作應全數出清"""
        command = TriggerExitCommand()
        result = command.execute(symbol="2330", action="SELL")

        assert result["action"] == "SELL"
        assert result["target_position_pct"] == 0
        assert result["urgency"] == "HIGH"

    def test_invalid_action_returns_error(self) -> None:
        """無效動作應返回錯誤"""
        command = TriggerExitCommand()
        result = command.execute(symbol="2330", action="INVALID")

        assert "error" in result

    def test_executed_flag_is_false(self) -> None:
        """executed 標記應為 False (需用戶確認)"""
        command = TriggerExitCommand()
        result = command.execute(symbol="2330", action="REDUCE")

        assert result["executed"] is False
