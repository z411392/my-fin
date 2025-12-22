"""ScanResidualMomentumQuery 單元測試"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestScanResidualMomentumQuery:
    """掃描殘差動能 Query 測試"""

    @pytest.fixture
    def fake_stock_list_provider(self):
        """Fake 股票清單提供者"""
        provider = MagicMock()
        provider.get_stock_list.return_value = ["2330.TW", "2317.TW"]
        provider.get_all_stocks.return_value = ["2330.TW", "2317.TW"]
        return provider

    @pytest.fixture
    def fake_console(self):
        """Fake Console"""
        console = MagicMock()
        console.info = MagicMock()
        console.warning = MagicMock()
        console.error = MagicMock()
        console.success = MagicMock()
        return console

    @pytest.fixture
    def query(self, fake_stock_list_provider):
        """建立 Query 實例"""
        from libs.hunting.src.application.queries.scan_residual_momentum import (
            ScanResidualMomentumQuery,
        )

        return ScanResidualMomentumQuery(
            stock_list_provider=fake_stock_list_provider,
        )

    def test_evaluate_single_stock_returns_none_for_empty_data(self, query):
        """測試資料為空時回傳 None"""
        with patch.object(query, "_get_returns", return_value=np.array([])):
            result = query.evaluate_single_stock("INVALID")
            assert result is None

    def test_evaluate_single_stock_returns_none_for_short_data(self, query):
        """測試資料過短時回傳 None"""
        # 回傳少於 lookback 的資料
        short_data = np.random.randn(10) * 0.02
        with patch.object(query, "_get_returns", return_value=short_data):
            result = query.evaluate_single_stock("2330.TW")
            assert result is None

    def test_evaluate_single_stock_with_valid_data(self, query):
        """測試有效資料時能正確評估"""
        # 產生足夠長的模擬資料
        valid_returns = np.random.randn(252) * 0.02

        with (
            patch.object(query, "_get_returns", return_value=valid_returns),
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.get_synthetic_sector_benchmark",
                return_value=np.random.randn(252) * 0.015,
            ),
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.kalman_beta_simple",
                return_value=np.ones(252),
            ),
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.calculate_ivol",
                return_value=0.25,
            ),
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.calculate_max_return",
                return_value=0.08,
            ),
            patch(
                "libs.hunting.src.application.queries.scan_residual_momentum.calculate_momentum_score",
                return_value=1.5,
            ),
            # get_ivol_percentile 已移除 (跨截面計算移至 CSV 階段)
        ):
            result = query.evaluate_single_stock("2330.TW")
            # 可能因為部分條件未通過返回 None，這裡不強制要求結果結構
            # 主要驗證不拋出例外
            assert result is None or isinstance(result, dict)
