"""GLI Liquidity Pulse Calculator

Corresponds to methodology.md §3 Market Physics and Global Monitoring
Global Liquidity Index Z-Score calculation
"""

import numpy as np


def calculate_gli_pulse(
    fed_balance: float,
    m2_yoy: float,
    historical_gli: np.ndarray,
) -> tuple[float, str]:
    """
    計算 GLI 流動性脈衝 Z-Score

    對應 methodology.md:
    - GLI Z > +2σ: 流動性海嘯，全面做多風險資產
    - GLI Z 0~+2σ: 正常擴張
    - GLI Z -2σ~0: 流動性收縮，減倉防禦
    - GLI Z < -2σ: 流動性乾涸，現金為王

    Args:
        fed_balance: Fed 資產負債表規模
        m2_yoy: M2 年增率
        historical_gli: 歷史 GLI 值序列

    Returns:
        tuple: (z_score, 狀態描述)
    """
    # 加權組合
    gli = fed_balance * 0.6 + m2_yoy * 0.4

    if len(historical_gli) < 2:
        return 0.0, "資料不足"

    mean = np.mean(historical_gli)
    std = np.std(historical_gli)

    if std == 0:
        return 0.0, "Neutral"

    z_score = (gli - mean) / std

    # 按照 methodology.md 分類
    if z_score > 2:
        status = "流動性海嘯"
    elif z_score > 0:
        status = "正常擴張"
    elif z_score > -2:
        status = "流動性收縮"
    else:
        status = "流動性乾涸"

    return z_score, status


def get_gli_action(z_score: float) -> str:
    """Get recommended action for GLI Z-Score

    Corresponds to methodology.md:
    - > +2σ: Go all-in
    - 0~+2σ: Normal operations
    - -2σ~0: Defensive mode
    - < -2σ: Cash is king
    """
    if z_score > 2:
        return "Go all-in on risk assets"
    elif z_score > 0:
        return "Normal operations"
    elif z_score > -2:
        return "Defensive mode, reduce positions"
    else:
        return "Cash is king"
