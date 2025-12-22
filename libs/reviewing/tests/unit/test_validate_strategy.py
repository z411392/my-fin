"""ValidateStrategyQuery 單元測試"""

from libs.reviewing.src.application.queries.validate_strategy import (
    ValidateStrategyQuery,
)


class TestValidateStrategyQuery:
    """測試 ValidateStrategyQuery"""

    def test_execute_returns_validation_result(self) -> None:
        """應返回驗證結果"""
        query = ValidateStrategyQuery()
        result = query.execute(strategy="test_strategy", days=252)

        assert "strategy" in result
        assert "days" in result
        assert "sharpe_ratio" in result
        assert "dsr" in result
        assert "psr" in result
        assert "pbo" in result
        assert "verdict" in result
        assert "skill_level" in result

    def test_dsr_in_valid_range(self) -> None:
        """DSR 應在 0-1 範圍內"""
        query = ValidateStrategyQuery()
        result = query.execute()

        assert 0 <= result["dsr"] <= 1

    def test_psr_in_valid_range(self) -> None:
        """PSR 應在 0-1 範圍內"""
        query = ValidateStrategyQuery()
        result = query.execute()

        assert 0 <= result["psr"] <= 1

    def test_pbo_in_valid_range(self) -> None:
        """PBO 應在 0-1 範圍內"""
        query = ValidateStrategyQuery()
        result = query.execute()

        assert 0 <= result["pbo"] <= 1
