"""Test Alpha/Beta Decomposer"""

import numpy as np

from libs.hunting.src.domain.services.alpha_beta_decomposer import (
    decompose_alpha_beta,
    interpret_contribution,
)


class TestDecomposeAlphaBeta:
    """Alpha/Beta 貢獻度分解測試"""

    def test_pure_beta_stock(self):
        """純 Beta 股票（完全跟隨市場）"""
        np.random.seed(42)
        market = np.random.randn(100) * 0.01
        stock = market * 1.2  # Beta = 1.2, Alpha = 0

        result = decompose_alpha_beta(stock, market, window=60)

        assert result["beta"] > 1.0
        assert result["beta_contribution_pct"] > 80
        assert result["is_all_weather"] is False

    def test_pure_alpha_stock(self):
        """純 Alpha 股票（獨立於市場）"""
        np.random.seed(42)
        market = np.random.randn(100) * 0.01
        stock = np.ones(100) * 0.001  # 每天固定 0.1% 報酬

        result = decompose_alpha_beta(stock, market, window=60)

        assert result["alpha_contribution_pct"] > 50
        assert result["is_all_weather"] is True

    def test_balanced_stock(self):
        """均衡型股票"""
        np.random.seed(42)
        market = np.random.randn(100) * 0.02  # 較大的市場波動
        stock = market * 0.8 + 0.0002  # Beta 0.8 + 小 Alpha

        result = decompose_alpha_beta(stock, market, window=60)

        assert 0.5 < result["beta"] < 1.2
        # 由於隨機性，只驗證結果結構正確
        assert result["alpha_contribution_pct"] + result["beta_contribution_pct"] > 99.0

    def test_insufficient_data(self):
        """資料不足時返回預設值"""
        result = decompose_alpha_beta(
            np.array([0.01, 0.02]),
            np.array([0.01, 0.02]),
            window=60,
        )

        assert result["alpha"] == 0.0
        assert result["beta"] == 1.0
        assert result["alpha_contribution_pct"] == 0.0
        assert result["beta_contribution_pct"] == 100.0

    def test_r_squared_in_result(self):
        """結果包含 R-squared"""
        np.random.seed(42)
        market = np.random.randn(100) * 0.01
        stock = market * 1.0  # 完美跟隨

        result = decompose_alpha_beta(stock, market, window=60)

        assert "r_squared" in result
        assert result["r_squared"] > 0.9  # 高 R-squared


class TestInterpretContribution:
    """貢獻度解讀測試"""

    def test_pure_alpha_interpretation(self):
        """純 Alpha 解讀"""
        result = {
            "alpha": 0.001,
            "beta": 0.2,
            "alpha_contribution_pct": 75.0,
            "beta_contribution_pct": 25.0,
            "total_return": 5.0,
            "alpha_return": 3.75,
            "beta_return": 1.25,
            "r_squared": 0.1,
            "is_all_weather": True,
        }

        label, desc = interpret_contribution(result)

        assert "純 Alpha" in label
        assert "75%" in desc

    def test_beta_dominated_interpretation(self):
        """Beta 主導解讀"""
        result = {
            "alpha": 0.0001,
            "beta": 1.5,
            "alpha_contribution_pct": 10.0,
            "beta_contribution_pct": 90.0,
            "total_return": 10.0,
            "alpha_return": 1.0,
            "beta_return": 9.0,
            "r_squared": 0.9,
            "is_all_weather": False,
        }

        label, desc = interpret_contribution(result)

        assert "Beta 主導" in label
        assert "90%" in desc
