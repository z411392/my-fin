"""GetSkillMetricsQuery 單元測試

遵循 testing.md Classicist 規範
"""

import pytest
from libs.reviewing.src.application.queries.get_skill_metrics import (
    GetSkillMetricsQuery,
)


class TestGetSkillMetricsQuery:
    """測試 GetSkillMetricsQuery"""

    @pytest.fixture
    def query(self):
        """建立 Query 實例 (portfolio_provider=None 使用 fallback)"""
        return GetSkillMetricsQuery(portfolio_provider=None)

    def test_execute_returns_skill_metrics(self, query) -> None:
        """應返回技能指標"""
        result = query.execute()

        assert "strategy" in result
        assert "sharpe_ratio" in result
        assert "dsr" in result
        assert "psr" in result
        assert "skill_level" in result
        assert "win_rate" in result
        assert "profit_factor" in result
        assert "max_drawdown" in result

    def test_dsr_in_valid_range(self, query) -> None:
        """DSR 應在 0-1 範圍內"""
        result = query.execute()

        assert 0 <= result["dsr"] <= 1

    def test_psr_in_valid_range(self, query) -> None:
        """PSR 應在 0-1 範圍內"""
        result = query.execute()

        assert 0 <= result["psr"] <= 1

    def test_win_rate_in_valid_range(self, query) -> None:
        """勝率應在 0-1 範圍內"""
        result = query.execute()

        assert 0 <= result["win_rate"] <= 1

    def test_confidence_is_string(self, query) -> None:
        """信心程度應為字串"""
        result = query.execute()

        assert isinstance(result["confidence"], str)

    def test_is_skill_is_boolean(self, query) -> None:
        """is_skill 應為布林值"""
        result = query.execute()

        assert isinstance(result["is_skill"], bool)
