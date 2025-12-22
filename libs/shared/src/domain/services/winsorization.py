"""Winsorization 縮尾工具

數據預處理：將極端值縮尾至指定百分位數範圍
用於消除異常值對統計計算的影響

參考: 《全球流動性因子與量化投資》數據處理章節
"""

import numpy as np
from numpy.typing import NDArray


def winsorize(
    data: NDArray[np.floating],
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
) -> NDArray[np.floating]:
    """對數據進行縮尾處理

    將低於 lower_percentile 的值設為該百分位數的值
    將高於 upper_percentile 的值設為該百分位數的值

    Args:
        data: 輸入數據陣列
        lower_percentile: 下界百分位數 (0-100)
        upper_percentile: 上界百分位數 (0-100)

    Returns:
        縮尾後的數據陣列

    Examples:
        >>> data = np.array([1, 2, 3, 100, 200])
        >>> winsorize(data, 10, 90)  # 將極端值縮尾
    """
    if len(data) == 0:
        return data

    lower_bound = np.percentile(data, lower_percentile)
    upper_bound = np.percentile(data, upper_percentile)

    return np.clip(data, lower_bound, upper_bound)


def winsorize_by_std(
    data: NDArray[np.floating],
    n_std: float = 3.0,
) -> NDArray[np.floating]:
    """使用標準差進行縮尾處理

    將超過 mean ± n_std * std 的值縮尾

    Args:
        data: 輸入數據陣列
        n_std: 標準差倍數 (預設 3 倍)

    Returns:
        縮尾後的數據陣列
    """
    if len(data) == 0:
        return data

    mean = np.mean(data)
    std = np.std(data)

    lower_bound = mean - n_std * std
    upper_bound = mean + n_std * std

    return np.clip(data, lower_bound, upper_bound)


def winsorize_mad(
    data: NDArray[np.floating],
    n_mad: float = 3.0,
) -> NDArray[np.floating]:
    """使用中位數絕對離差 (MAD) 進行縮尾處理

    MAD 對極端值更穩健，適用於重尾分佈

    Args:
        data: 輸入數據陣列
        n_mad: MAD 倍數 (預設 3 倍)

    Returns:
        縮尾後的數據陣列
    """
    if len(data) == 0:
        return data

    median = np.median(data)
    mad = np.median(np.abs(data - median))

    # MAD 轉換為標準差等價 (正態分佈下 MAD ≈ 0.6745 * std)
    mad_std = mad * 1.4826

    lower_bound = median - n_mad * mad_std
    upper_bound = median + n_mad * mad_std

    return np.clip(data, lower_bound, upper_bound)
