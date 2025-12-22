"""Kelly Position Calculator

Corresponds to algorithms.md §2.4
Regime-Adjusted Kelly Formula
"""

from libs.shared.src.enums.vix_tier import VixTier


def calculate_kelly_position(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    regime_factor: float,
    vix_factor: float,
    max_position: float = 0.10,
) -> float:
    """
    Calculate regime-adjusted Kelly position

    f_final = K_regime × K_VIX × (bp - q) / b

    Args:
        win_rate: Win rate (0-1)
        avg_win: Average gain
        avg_loss: Average loss (positive value)
        regime_factor: Regime factor (0-0.5)
        vix_factor: VIX factor (0-1)
        max_position: Maximum position per single target

    Returns:
        float: Recommended position ratio (0 - max_position)
    """
    if avg_loss == 0:
        return 0.0

    # Odds ratio
    b = avg_win / abs(avg_loss)
    p = win_rate
    q = 1 - p

    # Base Kelly
    kelly_base = (b * p - q) / b if b > 0 else 0

    # Regime adjustment
    kelly_final = regime_factor * vix_factor * kelly_base

    # Upper and lower bounds
    return min(max(kelly_final, 0), max_position)


def get_regime_factor(regime: str) -> float:
    """
    Get Kelly factor corresponding to regime

    Args:
        regime: Regime name

    Returns:
        float: K_regime (0-0.5)
    """
    factors = {
        "趨勢牛市": 0.5,
        "TREND_BULL": 0.5,
        "震盪區間": 0.25,
        "RANGE_BOUND": 0.25,
        "恐慌熊市": 0.0,
        "PANIC_BEAR": 0.0,
        "事件密集期": 0.25,  # Scenario dependent
        "EVENT_DRIVEN": 0.25,
    }
    return factors.get(regime, 0.25)


def get_vix_factor(vix_tier: VixTier) -> float:
    """
    Get Kelly factor corresponding to VIX

    Args:
        vix_tier: VIX fear ladder tier

    Returns:
        float: K_VIX (0-1)
    """
    factors = {
        VixTier.TIER_0: 1.0,
        VixTier.TIER_1: 0.5,
        VixTier.TIER_2: 0.25,
        VixTier.TIER_3: 0.0,
    }
    return factors.get(vix_tier, 0.0)
