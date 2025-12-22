"""GenerateWeeklyReviewCommand 單元測試"""

from libs.reviewing.src.application.commands.generate_weekly_review import (
    GenerateWeeklyReviewCommand,
)


class TestGenerateWeeklyReviewCommand:
    """測試 GenerateWeeklyReviewCommand"""

    def test_execute_returns_review(self) -> None:
        """應返回週度回顧"""
        command = GenerateWeeklyReviewCommand()
        result = command.execute()

        assert "week" in result or "month" in result  # 兼容過渡期
        assert "year" in result
        assert "performance" in result

    def test_performance_has_sharpe(self) -> None:
        """績效應包含 Sharpe Ratio"""
        command = GenerateWeeklyReviewCommand()
        result = command.execute()

        performance = result["performance"]
        assert "sharpe_ratio" in performance

    def test_includes_skill_assessment(self) -> None:
        """應包含技能評估"""
        command = GenerateWeeklyReviewCommand()
        result = command.execute()

        assert "skill_assessment" in result
