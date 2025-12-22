"""SNDZ 標準化器單元測試"""

import numpy as np

from libs.hunting.src.domain.services.sndz_standardizer import (
    standardize_zscore,
    standardize_robust,
    standardize_minmax,
    standardize_rank,
    standardize_sndz,
)


class TestStandardizeZscore:
    """測試 Z-Score 標準化"""

    def test_zscore_has_zero_mean(self) -> None:
        """Z-Score 標準化後均值應接近 0"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize_zscore(data)

        assert abs(np.mean(result)) < 1e-10

    def test_zscore_has_unit_std(self) -> None:
        """Z-Score 標準化後標準差應接近 1"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize_zscore(data)

        assert abs(np.std(result) - 1.0) < 1e-10

    def test_zscore_empty_array(self) -> None:
        """空陣列應返回空陣列"""
        data = np.array([])
        result = standardize_zscore(data)

        assert len(result) == 0

    def test_zscore_constant_array(self) -> None:
        """常數陣列應返回零陣列"""
        data = np.array([5.0, 5.0, 5.0, 5.0])
        result = standardize_zscore(data)

        assert np.all(result == 0.0)


class TestStandardizeRobust:
    """測試穩健標準化"""

    def test_robust_uses_median(self) -> None:
        """穩健標準化應使用中位數"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 100.0])  # 有極端值
        result = standardize_robust(data)

        # 中位數是 3，所以 3 標準化後應接近 0
        median_idx = 2
        assert abs(result[median_idx]) < 0.1

    def test_robust_empty_array(self) -> None:
        """空陣列應返回空陣列"""
        data = np.array([])
        result = standardize_robust(data)

        assert len(result) == 0


class TestStandardizeMinmax:
    """測試 Min-Max 標準化"""

    def test_minmax_default_range(self) -> None:
        """預設範圍應為 [0, 1]"""
        data = np.array([0.0, 50.0, 100.0])
        result = standardize_minmax(data)

        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_minmax_custom_range(self) -> None:
        """應支援自訂輸出範圍"""
        data = np.array([0.0, 50.0, 100.0])
        result = standardize_minmax(data, feature_range=(-1.0, 1.0))

        assert result.min() >= -1.0
        assert result.max() <= 1.0

    def test_minmax_empty_array(self) -> None:
        """空陣列應返回空陣列"""
        data = np.array([])
        result = standardize_minmax(data)

        assert len(result) == 0


class TestStandardizeRank:
    """測試秩標準化"""

    def test_rank_range_zero_to_one(self) -> None:
        """秩標準化範圍應為 [0, 1]"""
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        result = standardize_rank(data)

        assert result.min() == 0.0
        assert result.max() == 1.0

    def test_rank_preserves_order(self) -> None:
        """秩應保持原始順序"""
        data = np.array([30.0, 10.0, 50.0, 20.0, 40.0])
        result = standardize_rank(data)

        # 重新排序後應為 [0, 0.25, 0.5, 0.75, 1.0]
        assert result[1] < result[3] < result[0] < result[4] < result[2]

    def test_rank_empty_array(self) -> None:
        """空陣列應返回空陣列"""
        data = np.array([])
        result = standardize_rank(data)

        assert len(result) == 0


class TestStandardizeSndz:
    """測試 SNDZ 標準化 (Inverse Normal Transform)"""

    def test_sndz_approximately_normal(self) -> None:
        """SNDZ 結果應近似標準正態分佈 N(0,1)"""
        np.random.seed(42)
        # 使用偏態分佈測試
        data = np.exp(np.random.randn(100))  # Log-normal 分佈
        result = standardize_sndz(data)

        # 均值應接近 0，標準差應接近 1
        assert abs(np.mean(result)) < 0.2
        assert abs(np.std(result) - 1.0) < 0.2

    def test_sndz_empty_array(self) -> None:
        """空陣列應返回空陣列"""
        data = np.array([])
        result = standardize_sndz(data)

        assert len(result) == 0

    def test_sndz_single_element(self) -> None:
        """單元素陣列應返回零"""
        data = np.array([42.0])
        result = standardize_sndz(data)

        assert result[0] == 0.0

    def test_sndz_preserves_order(self) -> None:
        """SNDZ 應保持原始順序"""
        data = np.array([1.0, 5.0, 10.0, 50.0, 100.0])
        result = standardize_sndz(data)

        # 順序應保持：min -> max
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]
