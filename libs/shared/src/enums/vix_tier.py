"""VIX Fear Tier Enum

Corresponds to methodology.md §3 Market Physics and Global Monitoring
"""

from enum import Enum


class VixTier(Enum):
    """VIX Fear Tier"""

    TIER_0 = "Calm (100% Exposure)"  # VIX < 15
    TIER_1 = "Alert (75% Exposure)"  # VIX 15-25
    TIER_2 = "Tense (50% Exposure)"  # VIX 25-40
    TIER_3 = "Panic (25% Exposure)"  # VIX > 40
