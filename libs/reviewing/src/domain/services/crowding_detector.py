"""擁擠度偵測器

對應 prd.md §4.3
監控策略擁擠度與 Alpha 衰減
"""

import numpy as np

from libs.shared.src.dtos.reviewing.crowding_result_dto import (
    CrowdingResultDTO as CrowdingResult,
)


def calculate_pairwise_correlation(
    returns_matrix: np.ndarray,
) -> float:
    """
    計算投資組合成分的平均成對相關性

    Args:
        returns_matrix: 報酬矩陣 (時間 × 標的)

    Returns:
        float: 平均成對相關性
    """
    if returns_matrix.shape[1] < 2:
        return 0.0

    corr_matrix = np.corrcoef(returns_matrix.T)
    n = corr_matrix.shape[0]

    # 取上三角矩陣 (不含對角線)
    upper_tri = corr_matrix[np.triu_indices(n, k=1)]
    return float(np.mean(upper_tri))


def calculate_days_to_cover(
    position_value: float,
    avg_daily_volume: float,
) -> float:
    """
    計算平倉所需天數

    Args:
        position_value: 持倉價值
        avg_daily_volume: 平均日成交量

    Returns:
        float: 平倉天數
    """
    if avg_daily_volume <= 0:
        return float("inf")
    return position_value / avg_daily_volume


def estimate_alpha_half_life(
    alpha_series: np.ndarray,
) -> float:
    """
    估計 Alpha 半衰期

    Args:
        alpha_series: Alpha 序列

    Returns:
        float: 半衰期 (週)
    """
    if len(alpha_series) < 4:
        return float("inf")

    # 計算滾動均值的衰減
    rolling_mean = np.convolve(alpha_series, np.ones(4) / 4, mode="valid")

    if len(rolling_mean) < 2:
        return float("inf")

    # 估計衰減率
    if rolling_mean[0] != 0:
        decay_rate = rolling_mean[-1] / rolling_mean[0]
        if 0 < decay_rate < 1:
            half_life = -np.log(2) / np.log(decay_rate) * len(rolling_mean) / 12
            return float(half_life) if np.isfinite(half_life) else float("inf")

    return float("inf")


def assess_crowding(
    pairwise_corr: float,
    days_to_cover: float,
    dsr: float,
    alpha_half_life: float,
) -> CrowdingResult:
    """
    評估策略擁擠度

    Args:
        pairwise_corr: 成對相關性
        days_to_cover: 平倉天數
        dsr: Deflated Sharpe Ratio
        alpha_half_life: Alpha 半衰期

    Returns:
        CrowdingResult: 擁擠度評估結果
    """
    warnings = []
    actions = []

    # 成對相關性檢查
    if pairwise_corr > 0.8:
        warnings.append("高相關性")
        actions.append("減倉因子曝險")

    # 流動性檢查
    if days_to_cover > 10:
        warnings.append("流動性風險")
        actions.append("流動性危機預警")

    # DSR 檢查
    if dsr < 0.95:
        warnings.append("策略退役")
        actions.append("策略退役警示")

    # Alpha 半衰期檢查
    if alpha_half_life < 2:  # 小於 2 週
        warnings.append("Alpha 衰減")
        actions.append("取消交易")

    if warnings:
        status = " + ".join(warnings)
        action = "; ".join(actions)
    else:
        status = "正常"
        action = "維持策略"

    return {
        "pairwise_correlation": pairwise_corr,
        "days_to_cover": days_to_cover,
        "dsr": dsr,
        "alpha_half_life": alpha_half_life,
        "status": status,
        "action": action,
    }
