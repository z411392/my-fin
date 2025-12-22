"""TriggerDoubleLoopLearningCommand 單元測試"""

from libs.reviewing.src.application.commands.trigger_double_loop_learning import (
    TriggerDoubleLoopLearningCommand,
)


class TestTriggerDoubleLoopLearningCommand:
    """測試 TriggerDoubleLoopLearningCommand"""

    def test_execute_returns_learning_event(self) -> None:
        """應返回學習事件"""
        command = TriggerDoubleLoopLearningCommand()
        result = command.execute(strategy="test_strategy", reason="測試觸發")

        assert "strategy" in result
        assert "reason" in result
        assert "trigger_conditions" in result
        assert "hypothesis_review" in result
        assert "recommendations" in result
        assert result["strategy"] == "test_strategy"
        assert result["reason"] == "測試觸發"

    def test_trigger_conditions_identified(self) -> None:
        """應識別觸發條件"""
        command = TriggerDoubleLoopLearningCommand()
        result = command.execute()

        conditions = result["trigger_conditions"]
        assert len(conditions) > 0
        for cond in conditions:
            assert "condition" in cond
            assert "severity" in cond

    def test_hypothesis_review_generated(self) -> None:
        """應生成假設檢視清單"""
        command = TriggerDoubleLoopLearningCommand()
        result = command.execute(strategy="residual_momentum")

        review = result["hypothesis_review"]
        assert len(review) > 0
        for item in review:
            assert "hypothesis" in item
            assert "status" in item

    def test_recommendations_generated(self) -> None:
        """應生成改進建議"""
        command = TriggerDoubleLoopLearningCommand()
        result = command.execute()

        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        for rec in recommendations:
            assert "action" in rec
            assert "priority" in rec

    def test_learning_type_is_double_loop(self) -> None:
        """學習類型應為雙環學習"""
        command = TriggerDoubleLoopLearningCommand()
        result = command.execute()

        assert result["learning_type"] == "雙環學習"
