"""波動率縮放器 (Volatility Scaler)

根據波動率動態調整部位規模。
對應 diff.md §5.2 動態波動率縮放

公式:
Position_t = Position_target * (Vol_target / Vol_t)

原理：
當擁擠度上升或市場恐慌時，殘差波動率通常會擴張。
透過固定波動率目標 (Volatility Targeting)，我們能自動在風險升高時減倉，
實現「被動出場」。
"""

from libs.shared.src.dtos.hunting.scaling_result_dto import ScalingResultDTO


def scale_position_by_volatility(
    base_position_size: float,
    current_volatility: float,
    target_volatility: float = 0.15,  # 預設目標波動率 15%
    min_scaling: float = 0.25,  # 最小縮放倍數 (最多砍 75%)
    max_scaling: float = 2.0,  # 最大縮放倍數 (最多放大 2 倍)
) -> ScalingResultDTO:
    """
    根據波動率縮放部位

    Args:
        base_position_size: 基礎部位規模 (例如 0.05 = 5%)
        current_volatility: 當前波動率 (年化)
        target_volatility: 目標波動率 (年化)
        min_scaling: 最小縮放下限
        max_scaling: 最大縮放上限

    Returns:
        ScalingResult: 縮放結果
    """
    if current_volatility <= 0:
        return {
            "original_position": base_position_size,
            "adjusted_position": base_position_size,
            "scaling_factor": 1.0,
            "action": "KEEP",
            "reason": "波動率數據無效",
        }

    # 計算原始縮放比例
    raw_ratio = target_volatility / current_volatility

    # 套用限制
    scaling_factor = max(min_scaling, min(max_scaling, raw_ratio))

    adjusted_position = base_position_size * scaling_factor

    # 決定動作標籤
    if scaling_factor < 0.9:
        action = "REDUCE"
        reason = f"波動率偏高 ({current_volatility:.1%} > {target_volatility:.1%})"
    elif scaling_factor > 1.1:
        action = "EXPAND"
        reason = f"波動率偏低 ({current_volatility:.1%} < {target_volatility:.1%})"
    else:
        action = "KEEP"
        reason = "波動率在目標範圍內"

    return {
        "original_position": base_position_size,
        "adjusted_position": adjusted_position,
        "scaling_factor": scaling_factor,
        "action": action,
        "reason": reason,
    }
