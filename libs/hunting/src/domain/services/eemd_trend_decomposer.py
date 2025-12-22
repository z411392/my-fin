"""EEMD 趨勢分解器

對應 algorithms.md §2.3
使用 EEMD 分解累積殘差確認趨勢
"""

import numpy as np


def eemd_trend_simple(
    cumulative_residual: np.ndarray,
    pad_len: int = 21,
) -> tuple[np.ndarray, float, int]:
    """
    簡化版 EEMD 趨勢分解 (不依賴 PyEMD)

    使用滾動平均模擬趨勢提取

    Args:
        cumulative_residual: 累積殘差序列
        pad_len: 填充長度

    Returns:
        tuple: (trend_signal, current_slope, trend_days)
    """
    if len(cumulative_residual) < pad_len * 2:
        return cumulative_residual, 0.0, 0

    # 鏡像延拓避免邊界效應
    padded = np.pad(cumulative_residual, pad_width=pad_len, mode="reflect")

    # 使用多層滾動平均模擬 EEMD 趨勢提取
    # 第一層: 短期平滑
    window1 = min(5, len(padded) // 4)
    if window1 > 0:
        smooth1 = np.convolve(padded, np.ones(window1) / window1, mode="same")
    else:
        smooth1 = padded

    # 第二層: 中期平滑
    window2 = min(21, len(smooth1) // 4)
    if window2 > 0:
        smooth2 = np.convolve(smooth1, np.ones(window2) / window2, mode="same")
    else:
        smooth2 = smooth1

    # 切除填充
    trend_signal = smooth2[pad_len:-pad_len] if pad_len > 0 else smooth2

    # 確保長度一致
    if len(trend_signal) != len(cumulative_residual):
        trend_signal = cumulative_residual

    # 計算斜率 (過去 5 天)
    n = min(5, len(trend_signal))
    if n > 1:
        slope = (trend_signal[-1] - trend_signal[-n]) / n
    else:
        slope = 0.0

    # 計算連續正斜率天數
    trend_days = 0
    for i in range(len(trend_signal) - 1, 0, -1):
        if trend_signal[i] > trend_signal[i - 1]:
            trend_days += 1
        else:
            break

    return trend_signal, float(slope), trend_days


def confirm_eemd_trend(slope: float, trend_days: int, min_days: int = 3) -> bool:
    """確認 EEMD 趨勢是否有效"""
    return slope > 0 and trend_days >= min_days


def interpret_eemd_trend(slope: float, trend_days: int) -> tuple[str, str]:
    """解讀 EEMD 趨勢"""
    if slope > 0 and trend_days >= 5:
        return "強勢上升", "可進場"
    elif slope > 0 and trend_days >= 3:
        return "上升確認", "觀察進場"
    elif slope > 0:
        return "初期上升", "等待確認"
    elif slope < 0:
        return "下降趨勢", "避免進場"
    else:
        return "橫盤", "無方向"
