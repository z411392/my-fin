"""ValidateStrategyQQuery 單元測試

遵循 testing.md Classicist 規範
"""

import pytest
from unittest.mock import patch

from libs.reviewing.src.application.queries.validate_strategy_q import (
    ValidateStrategyQQuery,
)


class TestValidateStrategyQQuery:
    """策略驗證查詢測試 (Q 版)"""

    @pytest.fixture
    def query(self):
        """建立 Query 實例 (portfolio_provider=None 使用 fallback)"""
        return ValidateStrategyQQuery(portfolio_provider=None)

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_uses_sample_data_without_api_key(self, query) -> None:
        """無 API Key 時應使用 Mock 數據"""
        result = query.execute(strategy="test", days=252)

        assert result["data_source"] == "Mock"
        assert result["strategy"] == "test"
        assert result["days"] == 252

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_returns_sharpe_ratio(self, query) -> None:
        """應返回 Sharpe Ratio"""
        result = query.execute()

        assert "sharpe_ratio" in result
        assert isinstance(result["sharpe_ratio"], (int, float))

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_returns_dsr_and_psr(self, query) -> None:
        """應返回 DSR 和 PSR"""
        result = query.execute()

        assert "dsr" in result
        assert "psr" in result
        assert 0 <= result["psr"] <= 1  # PSR 介於 0-1

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_returns_skill_level(self, query) -> None:
        """應返回技能等級判定"""
        result = query.execute()

        assert "skill_level" in result
        valid_levels = ["Luck Dominated", "Indeterminate", "Possibly Skilled", "Skill Dominated"]
        assert result["skill_level"] in valid_levels

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_consistent_with_seed(self, query) -> None:
        """Mock 模式應產生一致結果 (固定種子)"""
        result1 = query.execute(days=100)
        result2 = query.execute(days=100)

        # 因為使用固定種子 42，結果應一致
        assert result1["sharpe_ratio"] == result2["sharpe_ratio"]

    @patch.dict("os.environ", {"SHIOAJI_API_KEY": ""}, clear=False)
    def test_execute_different_days(self, query) -> None:
        """不同天數應影響結果"""
        result_short = query.execute(days=30)
        result_long = query.execute(days=252)

        assert result_short["days"] == 30
        assert result_long["days"] == 252
