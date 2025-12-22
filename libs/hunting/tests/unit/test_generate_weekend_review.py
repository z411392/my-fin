"""GenerateWeekendReviewCommand 單元測試"""

import pytest
import unittest
import unittest.mock
from libs.hunting.src.application.commands.generate_weekend_review import (
    GenerateWeekendReviewCommand,
)


class TestGenerateWeekendReviewCommand:
    """測試 GenerateWeekendReviewCommand"""

    @pytest.fixture
    def fake_yf(self):
        """Fake yfinance"""
        with unittest.mock.patch("yfinance.Ticker") as stub:
            # Mock history DataFrame
            import pandas as pd
            import numpy as np

            dates = pd.date_range(start="2024-01-01", periods=100)
            df = pd.DataFrame({"Close": np.random.normal(100, 10, 100)}, index=dates)

            # Configure stub to return DataFrame
            stub.return_value.history.return_value = df
            yield stub

    def test_execute_returns_review(self, fake_yf) -> None:
        """應返回週末回顧"""
        command = GenerateWeekendReviewCommand()
        result = command.execute(watchlist=["AAPL", "NVDA"])

        assert "date" in result
        assert "momentum_candidates" in result
        assert "regime" in result

    def test_momentum_candidates_is_list(self, fake_yf) -> None:
        """動能候選應為列表"""
        command = GenerateWeekendReviewCommand()
        result = command.execute(watchlist=["AAPL"])

        assert isinstance(result["momentum_candidates"], list)

    def test_regime_has_hurst(self, fake_yf) -> None:
        """體制應包含 Hurst 指數"""
        command = GenerateWeekendReviewCommand()
        result = command.execute(watchlist=["AAPL"])

        regime = result["regime"]
        assert "hurst" in regime
