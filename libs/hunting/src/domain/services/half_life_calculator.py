"""半衰期計算器

計算殘差動能信號的半衰期與剩餘肉量
對應 diff.md §4.1 信號半衰期
"""

import math
import numpy as np


def calculate_half_life(residuals: np.ndarray) -> tuple[float, float]:
    """
    計算殘差序列的半衰期 (Ornstein-Uhlenbeck 過程估計)

    使用 AR(1) 迴歸估計 λ 參數：
    residual_t = ρ × residual_{t-1} + ε
    λ = -ln(ρ)
    HL = ln(2) / λ

    Args:
        residuals: 殘差序列 (日報酬)

    Returns:
        tuple: (半衰期天數, lambda 參數)
    """
    if len(residuals) < 10:
        return float("inf"), 0.0

    # AR(1) 迴歸: y_t = ρ × y_{t-1} + ε
    y = residuals[1:]
    x = residuals[:-1]

    # 最小二乘法估計 ρ
    if np.var(x) == 0:
        return float("inf"), 0.0

    rho = np.sum(x * y) / np.sum(x * x)

    # 確保 ρ 在有效範圍內
    if rho <= 0 or rho >= 1:
        return float("inf"), 0.0

    # 計算 λ 和半衰期
    lambda_param = -math.log(rho)
    half_life = math.log(2) / lambda_param

    return half_life, lambda_param


def calculate_signal_age(zscore_series: np.ndarray, threshold: float = 1.0) -> int:
    """
    計算信號年齡 (Z-Score 首次突破閾值至今的天數)

    Args:
        zscore_series: Z-Score 時間序列 (最新值在最後)
        threshold: 突破閾值 (預設 1.0)

    Returns:
        int: 信號年齡 (天數)，若未突破則返回 0
    """
    if len(zscore_series) == 0:
        return 0

    # 從最早往最新找第一個突破點
    for i, z in enumerate(zscore_series):
        if z >= threshold:
            # 從突破點到現在的天數
            return len(zscore_series) - i

    return 0


def calculate_remaining_meat(
    signal_age: int, half_life: float = 130
) -> tuple[float, str]:
    """
    計算剩餘肉量

    公式: Meat = e^{-Age/HL}

    Args:
        signal_age: 信號年齡 (天數)
        half_life: 半衰期 (預設 130 天 ≈ 6 個月)

    Returns:
        tuple: (剩餘肉量比例, 策略建議)
    """
    if half_life <= 0 or signal_age < 0:
        return 0.0, "資料異常"

    # 計算剩餘肉量
    remaining = math.exp(-signal_age / half_life)

    # 根據閾值判定策略建議
    if remaining >= 0.70:
        recommendation = "積極持有"
    elif remaining >= 0.50:
        recommendation = "維持但警覺"
    elif remaining >= 0.30:
        recommendation = "考慮減碼"
    else:
        recommendation = "準備出場"

    return remaining, recommendation


def get_lifecycle_stage(signal_age: int) -> tuple[str, str]:
    """
    根據信號年齡判定生命週期階段

    Args:
        signal_age: 信號年齡 (天數)

    Returns:
        tuple: (階段代碼, 階段描述)
    """
    # 轉換為月數 (約 22 交易日/月)
    months = signal_age / 22

    if months < 3:
        return "young", "🟢 年輕"
    elif months < 6:
        return "mature", "🟡 成熟"
    elif months < 9:
        return "aging", "🟠 老化"
    else:
        return "exhausted", "🔴 耗盡"


def interpret_lifecycle(
    signal_age: int, remaining_meat: float, half_life: float
) -> str:
    """
    解讀動能生命週期

    Args:
        signal_age: 信號年齡 (天數)
        remaining_meat: 剩餘肉量比例
        half_life: 半衰期 (天數)

    Returns:
        str: 人類可讀的解釋
    """
    stage_code, stage_desc = get_lifecycle_stage(signal_age)
    months = signal_age / 22

    if remaining_meat >= 0.70:
        return f"{stage_desc} | 信號年齡 {months:.1f}M | 剩餘肉量 {remaining_meat:.0%} ✅ 可積極持有"
    elif remaining_meat >= 0.50:
        return f"{stage_desc} | 信號年齡 {months:.1f}M | 剩餘肉量 {remaining_meat:.0%} ⚠️ 維持警覺"
    elif remaining_meat >= 0.30:
        return f"{stage_desc} | 信號年齡 {months:.1f}M | 剩餘肉量 {remaining_meat:.0%} 🟡 考慮減碼"
    else:
        return f"{stage_desc} | 信號年齡 {months:.1f}M | 剩餘肉量 {remaining_meat:.0%} 🔴 準備出場"
