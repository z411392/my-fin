"""Alpha/Beta 貢獻度分解器

對應 plan.md P0 項目
分解股票收益為 Alpha 貢獻與 Beta 貢獻百分比

參考: 多因子股票評價系統建構.md §3.1
"""

import numpy as np
from numpy.typing import NDArray

from libs.shared.src.dtos.hunting.alpha_beta_contribution_dto import (
    AlphaBetaContributionDTO,
)


def decompose_alpha_beta(
    stock_returns: NDArray[np.floating],
    market_returns: NDArray[np.floating],
    window: int = 60,
) -> AlphaBetaContributionDTO:
    """分解收益為 Alpha 與 Beta 貢獻

    使用線性回歸分解：
    R_stock = α + β × R_market + ε

    Alpha 貢獻 = α / Total Return
    Beta 貢獻 = β × R_market / Total Return

    Args:
        stock_returns: 股票日報酬序列
        market_returns: 市場日報酬序列 (如 SPY, 0050)
        window: 回歸視窗 (預設 60 日)

    Returns:
        AlphaBetaContributionDTO
    """
    if len(stock_returns) < window or len(market_returns) < window:
        return {
            "alpha": 0.0,
            "beta": 1.0,
            "alpha_contribution_pct": 0.0,
            "beta_contribution_pct": 100.0,
            "total_return": 0.0,
            "alpha_return": 0.0,
            "beta_return": 0.0,
            "r_squared": 0.0,
            "is_all_weather": False,
        }

    # Take most recent window periods
    y = stock_returns[-window:]
    x = market_returns[-window:]

    # Linear regression: y = alpha + beta * x
    x_mean = np.mean(x)
    y_mean = np.mean(y)

    cov_xy = np.sum((x - x_mean) * (y - y_mean))
    var_x = np.sum((x - x_mean) ** 2)

    if var_x < 1e-10:
        beta = 1.0
    else:
        beta = cov_xy / var_x

    alpha = y_mean - beta * x_mean

    # Calculate R-squared
    y_pred = alpha + beta * x
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-10 else 0.0

    # 累積報酬
    total_return = float(np.sum(y))
    alpha_return = float(alpha * window)  # Alpha 貢獻 = 每日 alpha × 天數
    beta_return = float(beta * np.sum(x))  # Beta 貢獻 = beta × 市場累積報酬

    # 計算貢獻百分比 (避免除以零)
    if abs(total_return) < 1e-10:
        alpha_contribution_pct = 50.0
        beta_contribution_pct = 50.0
    else:
        # 使用絕對值分配避免負值干擾
        abs_alpha = abs(alpha_return)
        abs_beta = abs(beta_return)
        total_abs = abs_alpha + abs_beta

        if total_abs < 1e-10:
            alpha_contribution_pct = 50.0
            beta_contribution_pct = 50.0
        else:
            alpha_contribution_pct = (abs_alpha / total_abs) * 100
            beta_contribution_pct = (abs_beta / total_abs) * 100

    # 全天候組合標記: Alpha 貢獻 > 50%
    is_all_weather = alpha_contribution_pct > 50.0

    return {
        "alpha": round(alpha, 6),
        "beta": round(beta, 4),
        "alpha_contribution_pct": round(alpha_contribution_pct, 1),
        "beta_contribution_pct": round(beta_contribution_pct, 1),
        "total_return": round(total_return * 100, 2),  # Convert to percentage
        "alpha_return": round(alpha_return * 100, 2),
        "beta_return": round(beta_return * 100, 2),
        "r_squared": round(r_squared, 4),
        "is_all_weather": is_all_weather,
    }


def interpret_contribution(result: AlphaBetaContributionDTO) -> tuple[str, str]:
    """解讀貢獻度結果

    Args:
        result: 分解結果

    Returns:
        tuple: (標籤, 說明)
    """
    alpha_pct = result["alpha_contribution_pct"]
    beta = result["beta"]

    if alpha_pct >= 70:
        label = "🌟 純 Alpha"
        desc = f"Alpha 貢獻 {alpha_pct:.0f}%，低市場依賴，全天候特性"
    elif alpha_pct >= 50:
        label = "☀️ Alpha 主導"
        desc = f"Alpha 貢獻 {alpha_pct:.0f}%，可納入全天候組合"
    elif alpha_pct >= 30:
        label = "🌤️ 均衡型"
        desc = f"Alpha/Beta 均衡，Beta={beta:.2f}"
    else:
        label = "📈 Beta 主導"
        desc = f"Beta 貢獻 {result['beta_contribution_pct']:.0f}%，隨市場波動"

    return label, desc
