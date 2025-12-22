"""VIX Fear Tier Calculator

Corresponds to methodology.md §3 Market Physics and Global Monitoring
Determines fear level and recommended action based on VIX value
"""

from libs.shared.src.enums.vix_tier import VixTier
from libs.shared.src.constants.vix_thresholds import (
    VIX_TIER_0_MAX,
    VIX_TIER_1_MAX,
    VIX_TIER_2_MAX,
)


def calculate_vix_tier(vix: float) -> tuple[VixTier, str, str]:
    """
    Calculate VIX fear tier level

    Corresponds to methodology.md:
    - VIX < 15: Calm, maintain 100% exposure
    - VIX 15-25: Alert, reduce to 75% exposure
    - VIX 25-40: Tense, reduce to 50% exposure
    - VIX > 40: Panic, reduce to 25% exposure or exit

    Args:
        vix: VIX index value

    Returns:
        tuple: (VixTier, emoji, recommended action)
    """
    if vix < VIX_TIER_0_MAX:
        return VixTier.TIER_0, "🟢", "Normal operation (100% exposure)"
    elif vix < VIX_TIER_1_MAX:
        return VixTier.TIER_1, "🟡", "Alert state (75% exposure)"
    elif vix < VIX_TIER_2_MAX:
        return VixTier.TIER_2, "🟠", "Market tension (50% exposure)"
    else:
        return VixTier.TIER_3, "🔴", "Market panic (25% exposure or exit)"


def get_vix_kelly_factor(tier: VixTier) -> float:
    """Get Kelly coefficient factor for VIX tier

    Corresponds to methodology.md:
    - TIER_0: 100% exposure → factor 1.0
    - TIER_1: 75% exposure → factor 0.75
    - TIER_2: 50% exposure → factor 0.50
    - TIER_3: 25% exposure → factor 0.25
    """
    factors = {
        VixTier.TIER_0: 1.0,
        VixTier.TIER_1: 0.75,
        VixTier.TIER_2: 0.50,
        VixTier.TIER_3: 0.25,
    }
    return factors.get(tier, 0.0)
