"""體制動態權重

Alpha-Core V4.0: 根據 HMM 狀態調整因子權重
"""

from libs.shared.src.dtos.hunting.factor_weights_dto import FactorWeightsDTO


def get_factor_weights(hmm_state: int, bull_prob: float) -> FactorWeightsDTO:
    """
    根據 HMM 狀態取得因子權重

    | HMM State | Trend 權重 | Value 權重 | Quality 權重 |
    |-----------|------------|------------|--------------|
    | 牛市      | 60%        | 20%        | 20%          |
    | 震盪      | 30%        | 40%        | 30%          |
    | 熊市      | 0%         | 50%        | 50%          |

    Args:
        hmm_state: HMM 狀態 (1=牛市, 0=熊市)
        bull_prob: 牛市機率 (0-1)

    Returns:
        dict: {trend_weight, value_weight, quality_weight}
    """
    # 牛市 (state=1, prob > 0.6)
    if hmm_state == 1 and bull_prob > 0.6:
        return {
            "trend": 0.60,
            "value": 0.20,
            "quality": 0.20,
            "regime": "BULL",
            "regime_emoji": "🟢",
        }

    # 熊市 (state=0, prob < 0.4)
    if hmm_state == 0 and bull_prob < 0.4:
        return {
            "trend": 0.00,
            "value": 0.50,
            "quality": 0.50,
            "regime": "BEAR",
            "regime_emoji": "🔴",
        }

    # 震盪 (中性)
    return {
        "trend": 0.30,
        "value": 0.40,
        "quality": 0.30,
        "regime": "NEUTRAL",
        "regime_emoji": "🟡",
    }


def apply_regime_weight(
    momentum_score: float,
    value_score: float,
    quality_score: float,
    weights: dict[str, float],
) -> float:
    """
    應用體制權重計算綜合分數

    Args:
        momentum_score: 動能分數 (標準化後)
        value_score: 價值分數 (標準化後)
        quality_score: 品質分數 (標準化後)
        weights: 權重字典

    Returns:
        加權綜合分數
    """
    return (
        momentum_score * weights.get("trend", 0.33)
        + value_score * weights.get("value", 0.33)
        + quality_score * weights.get("quality", 0.34)
    )
