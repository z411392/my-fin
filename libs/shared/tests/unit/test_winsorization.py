"""Winsorization Tool Unit Tests"""

import numpy as np

from libs.shared.src.domain.services.winsorization import (
    winsorize,
    winsorize_by_std,
    winsorize_mad,
)


class TestWinsorize:
    """Test winsorize function"""

    def test_winsorize_clips_extreme_values(self) -> None:
        """Should clip extreme values"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])
        result = winsorize(data, lower_percentile=10, upper_percentile=90)

        # 100 should be clipped to 90th percentile
        assert result.max() < 100.0
        assert result.min() >= 1.0

    def test_winsorize_empty_array(self) -> None:
        """Empty array should return empty array"""
        data = np.array([])
        result = winsorize(data)

        assert len(result) == 0

    def test_winsorize_preserves_middle_values(self) -> None:
        """Middle values should remain unchanged"""
        data = np.array([1.0, 50.0, 100.0])
        result = winsorize(data, lower_percentile=1, upper_percentile=99)

        assert result[1] == 50.0


class TestWinsorizeByStd:
    """Test winsorize_by_std function"""

    def test_clips_beyond_n_std(self) -> None:
        """Values beyond n std should be clipped"""
        # Create normal distribution data with outlier
        np.random.seed(42)
        normal_data = np.random.normal(loc=50, scale=5, size=100)
        data_with_outlier = np.append(normal_data, 1000.0)  # Significant outlier

        result = winsorize_by_std(data_with_outlier, n_std=3.0)

        # 1000 is far beyond mean + 3*std (approx 50 + 15 = 65), should be clipped
        assert result.max() < 1000.0
        # Most data should remain unchanged
        assert np.allclose(result[:-1], normal_data)

    def test_empty_array(self) -> None:
        """Empty array should return empty array"""
        data = np.array([])
        result = winsorize_by_std(data)

        assert len(result) == 0


class TestWinsorizeMad:
    """Test winsorize_mad function"""

    def test_clips_using_mad(self) -> None:
        """Should clip using MAD method"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 1000.0])
        result = winsorize_mad(data, n_mad=3.0)

        # Outlier 1000 should be clipped
        assert result.max() < 1000.0

    def test_empty_array(self) -> None:
        """Empty array should return empty array"""
        data = np.array([])
        result = winsorize_mad(data)

        assert len(result) == 0

    def test_mad_more_robust_than_std(self) -> None:
        """MAD should be more robust to outliers"""
        # Data with one outlier
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 10000.0])

        result_std = winsorize_by_std(data, n_std=3.0)
        result_mad = winsorize_mad(data, n_mad=3.0)

        # MAD method upper bound should be closer to normal data range
        assert result_mad.max() <= result_std.max()
