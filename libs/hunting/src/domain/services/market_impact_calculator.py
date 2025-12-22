"""Market Impact Calculator

計算市場衝擊成本，使用平方根法則。
根據 2_market_physics.md：Impact ≈ σ × √(Q/V)
"""

import math

from libs.shared.src.dtos.hunting.market_impact_result_dto import (
    MarketImpactResultDTO as MarketImpactResult,
)


def calculate_impact(
    order_size: float,
    adv: float,
    volatility: float,
    y_coefficient: float = 0.5,
) -> float:
    """
    計算市場衝擊成本 (平方根法則)

    Impact = Y × σ × √(Q/V)

    Args:
        order_size: 訂單規模 (股數或金額)
        adv: 日均成交量
        volatility: 日波動率 (如 0.02 代表 2%)
        y_coefficient: 台股特定係數 (預設 0.5，需校準)

    Returns:
        預估衝擊成本 (百分比)
    """
    if adv <= 0:
        return float("inf")

    participation_rate = order_size / adv

    if participation_rate <= 0:
        return 0.0

    impact = y_coefficient * volatility * math.sqrt(participation_rate)
    return impact


def should_execute_trade(
    expected_alpha: float,
    order_size: float,
    adv: float,
    volatility: float,
    y_coefficient: float = 0.5,
) -> bool:
    """
    判斷交易是否值得執行

    若 E[r] < E[c]，不執行交易

    Args:
        expected_alpha: 預期 Alpha (百分比)
        order_size: 訂單規模
        adv: 日均成交量
        volatility: 日波動率
        y_coefficient: 衝擊係數

    Returns:
        True 如果值得執行
    """
    expected_cost = calculate_impact(order_size, adv, volatility, y_coefficient)
    return expected_alpha > expected_cost


def assess_market_impact(
    order_size: float,
    adv: float,
    volatility: float,
    expected_alpha: float,
    y_coefficient: float = 0.5,
) -> MarketImpactResult:
    """
    完整評估市場衝擊

    Args:
        order_size: 訂單規模
        adv: 日均成交量
        volatility: 日波動率
        expected_alpha: 預期 Alpha
        y_coefficient: 衝擊係數

    Returns:
        MarketImpactResult 包含完整評估
    """
    estimated_impact = calculate_impact(order_size, adv, volatility, y_coefficient)
    participation_rate = order_size / adv if adv > 0 else float("inf")
    execute = should_execute_trade(
        expected_alpha, order_size, adv, volatility, y_coefficient
    )

    return MarketImpactResult(
        estimated_impact=estimated_impact,
        order_size=order_size,
        adv=adv,
        participation_rate=participation_rate,
        should_execute=execute,
    )


def calculate_optimal_order_size(
    expected_alpha: float,
    adv: float,
    volatility: float,
    y_coefficient: float = 0.5,
) -> float:
    """
    計算最佳訂單規模

    在 Impact = Alpha 時達到平衡點

    Args:
        expected_alpha: 預期 Alpha
        adv: 日均成交量
        volatility: 日波動率
        y_coefficient: 衝擊係數

    Returns:
        最佳訂單規模
    """
    if volatility <= 0 or y_coefficient <= 0:
        return 0.0

    # Impact = Y × σ × √(Q/V) = Alpha
    # √(Q/V) = Alpha / (Y × σ)
    # Q/V = (Alpha / (Y × σ))²
    # Q = V × (Alpha / (Y × σ))²

    ratio = expected_alpha / (y_coefficient * volatility)
    optimal_size = adv * (ratio**2)

    return optimal_size
