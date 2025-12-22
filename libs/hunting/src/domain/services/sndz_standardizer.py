"""SNDZ 標準化器 (Standardized Normalized Deviation Z-Score)

實作因子標準化流程：
1. 縮尾處理 (Winsorization)
2. Z-Score 標準化
3. 支援跨截面 (cross-sectional) 和時序 (time-series) 標準化

參考: plan.md Phase 1 數據基礎設施
"""

import numpy as np
from numpy.typing import NDArray

from libs.shared.src.domain.services.winsorization import winsorize


def standardize_zscore(
    data: NDArray[np.floating],
    winsorize_pct: tuple[float, float] = (1.0, 99.0),
) -> NDArray[np.floating]:
    """Z-Score 標準化 (帶縮尾)

    步驟:
    1. 縮尾處理極端值
    2. 計算 Z-Score: (x - mean) / std

    Args:
        data: 輸入數據陣列
        winsorize_pct: 縮尾百分位數 (lower, upper)

    Returns:
        標準化後的 Z-Score 陣列
    """
    if len(data) == 0:
        return data

    # 1. 縮尾處理
    winsorized = winsorize(data, winsorize_pct[0], winsorize_pct[1])

    # 2. Z-Score 標準化
    mean = np.mean(winsorized)
    std = np.std(winsorized)

    if std < 1e-10:  # 避免除以零
        return np.zeros_like(winsorized)

    return (winsorized - mean) / std


def standardize_robust(
    data: NDArray[np.floating],
    winsorize_pct: tuple[float, float] = (1.0, 99.0),
) -> NDArray[np.floating]:
    """穩健標準化 (使用中位數和 MAD)

    使用中位數和 MAD (Median Absolute Deviation) 替代均值和標準差
    對極端值更穩健

    Args:
        data: 輸入數據陣列
        winsorize_pct: 縮尾百分位數 (lower, upper)

    Returns:
        穩健標準化後的陣列
    """
    if len(data) == 0:
        return data

    # 1. 縮尾處理
    winsorized = winsorize(data, winsorize_pct[0], winsorize_pct[1])

    # 2. 穩健標準化
    median = np.median(winsorized)
    mad = np.median(np.abs(winsorized - median))

    # MAD 轉換常數 (正態分佈下)
    mad_std = mad * 1.4826

    if mad_std < 1e-10:
        return np.zeros_like(winsorized)

    return (winsorized - median) / mad_std


def standardize_minmax(
    data: NDArray[np.floating],
    winsorize_pct: tuple[float, float] = (1.0, 99.0),
    feature_range: tuple[float, float] = (0.0, 1.0),
) -> NDArray[np.floating]:
    """Min-Max 標準化 (帶縮尾)

    將數據縮放至指定範圍 [min_val, max_val]

    Args:
        data: 輸入數據陣列
        winsorize_pct: 縮尾百分位數 (lower, upper)
        feature_range: 輸出範圍 (min, max)

    Returns:
        縮放後的陣列
    """
    if len(data) == 0:
        return data

    # 1. 縮尾處理
    winsorized = winsorize(data, winsorize_pct[0], winsorize_pct[1])

    # 2. Min-Max 縮放
    data_min = np.min(winsorized)
    data_max = np.max(winsorized)
    data_range = data_max - data_min

    if data_range < 1e-10:
        return np.full_like(winsorized, feature_range[0])

    # 縮放至 [0, 1] 再轉換至目標範圍
    scaled = (winsorized - data_min) / data_range
    return scaled * (feature_range[1] - feature_range[0]) + feature_range[0]


def standardize_rank(
    data: NDArray[np.floating],
) -> NDArray[np.floating]:
    """秩標準化

    將數據轉換為百分位秩 [0, 1]
    對分佈無假設，完全非參數

    Args:
        data: 輸入數據陣列

    Returns:
        秩標準化後的陣列 (0 = 最小, 1 = 最大)
    """
    if len(data) == 0:
        return data

    # 使用 scipy 風格的秩計算
    from scipy import stats

    ranks = stats.rankdata(data, method="average")
    # 轉換為 [0, 1] 範圍的百分位
    return (ranks - 1) / (len(data) - 1) if len(data) > 1 else np.zeros_like(data)


def standardize_sndz(
    data: NDArray[np.floating],
) -> NDArray[np.floating]:
    """SNDZ 標準化 (Standard Normally Distributed Z-score on Percentile Rank)

    基於秩分的標準正態化，確保輸出嚴格服從 N(0,1) 分佈。
    無論原始因子分佈多麼怪異（偏態、多峰、厚尾），SNDZ 處理後的得分
    嚴格服從標準正態分佈，確保因子間的橫截面可比性。

    步驟:
    1. 過濾 NaN 值 (rankdata 無法處理 NaN)
    2. 計算百分位秩 (0, 1)
    3. 應用逆正態變換 (Inverse CDF, Φ^{-1})
    4. 將結果放回原位置，NaN 位置保持 NaN

    參考: S&P Global - Effective Scoring to Capture Quality and Value

    Args:
        data: 輸入數據陣列 (可包含 NaN)

    Returns:
        標準正態分佈的 Z-Score 陣列 N(0, 1)，NaN 位置保持 NaN

    Examples:
        >>> data = np.array([1.0, 5.0, 10.0, 50.0, 100.0])
        >>> sndz = standardize_sndz(data)
        >>> np.abs(np.mean(sndz)) < 0.1  # 均值接近 0
        True
        >>> np.abs(np.std(sndz) - 1.0) < 0.2  # 標準差接近 1
        True
    """
    if len(data) == 0:
        return data

    from scipy.stats import norm, rankdata

    # 處理 NaN: rankdata 無法處理 NaN，會導致全部輸出 NaN
    # 解決方案：過濾 NaN，計算 SNDZ，再放回原位置
    valid_mask = ~np.isnan(data)
    valid_data = data[valid_mask]

    if len(valid_data) == 0:
        return np.full_like(data, np.nan)

    if len(valid_data) == 1:
        result = np.full_like(data, np.nan)
        result[valid_mask] = 0.0
        return result

    # 1. 計算秩（處理相同值）
    ranks = rankdata(valid_data, method="average")

    # 2. 轉換為百分位秩 (0, 1)，避免 0 和 1（會導致 ppf 極端值）
    n = len(valid_data)
    percentile_ranks = (ranks - 0.5) / n

    # 3. 應用逆正態變換
    sndz_scores = norm.ppf(percentile_ranks)

    # 4. 將結果放回原位置，NaN 位置保持 NaN
    result = np.full_like(data, np.nan)
    result[valid_mask] = sndz_scores

    return result
