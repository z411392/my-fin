"""CVaR (Conditional Value at Risk) Calculator

計算 Conditional Value at Risk (Expected Shortfall)，取代傳統 VaR。
根據裁決報告：風險模型應使用 CVaR + 極值理論，而非常態分佈 VaR。
"""

import numpy as np
from scipy import stats

from libs.shared.src.dtos.reviewing.cvar_result_dto import CVaRResultDTO as CVaRResult


def calculate_var(returns: list[float], confidence_level: float = 0.95) -> float:
    """
    計算 Value at Risk (Historical Simulation)

    Args:
        returns: 歷史報酬序列
        confidence_level: 置信水準 (預設 95%)

    Returns:
        VaR 值 (負數代表損失)
    """
    if len(returns) == 0:
        return 0.0
    return float(np.percentile(returns, (1 - confidence_level) * 100))


def calculate_cvar(returns: list[float], confidence_level: float = 0.95) -> float:
    """
    計算 Conditional Value at Risk (Expected Shortfall)

    CVaR = E[Loss | Loss > VaR]
    即在超過 VaR 損失的情況下，預期的平均損失

    Args:
        returns: 歷史報酬序列
        confidence_level: 置信水準 (預設 95%)

    Returns:
        CVaR 值 (負數代表損失)
    """
    if len(returns) == 0:
        return 0.0

    var = calculate_var(returns, confidence_level)
    tail_returns = [r for r in returns if r <= var]

    if len(tail_returns) == 0:
        return var

    return float(np.mean(tail_returns))


def calculate_cvar_parametric(
    mean: float, std: float, confidence_level: float = 0.95
) -> float:
    """
    參數法計算 CVaR (假設常態分佈)

    Args:
        mean: 報酬均值
        std: 報酬標準差
        confidence_level: 置信水準

    Returns:
        CVaR 值
    """

    alpha = 1 - confidence_level
    z_alpha = stats.norm.ppf(alpha)
    phi_z = stats.norm.pdf(z_alpha)

    # CVaR for normal distribution
    cvar = mean - std * phi_z / alpha
    return cvar


def assess_tail_risk(
    returns: list[float], confidence_level: float = 0.95
) -> CVaRResult:
    """
    評估尾部風險

    Args:
        returns: 歷史報酬序列
        confidence_level: 置信水準

    Returns:
        CVaRResult 包含 VaR, CVaR, tail_ratio
    """
    var = calculate_var(returns, confidence_level)
    cvar = calculate_cvar(returns, confidence_level)

    # Tail ratio: CVaR / VaR
    # 比值越大，尾部風險越嚴重 (肥尾)
    tail_ratio = cvar / var if var != 0 else 1.0

    return CVaRResult(
        var=var,
        cvar=cvar,
        confidence_level=confidence_level,
        tail_ratio=tail_ratio,
    )
