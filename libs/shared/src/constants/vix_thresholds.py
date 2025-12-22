"""VIX Fear Ladder Thresholds

Corresponds to methodology.md §3 Market Physics and Global Monitoring
"""

# VIX Tier boundaries (methodology.md definition)
VIX_TIER_0_MAX = 15  # Calm: maintain 100% exposure
VIX_TIER_1_MAX = 25  # Alert: reduce to 75% exposure
VIX_TIER_2_MAX = 40  # Tense: reduce to 50% exposure
VIX_TIER_3_PANIC = 40  # Panic threshold: reduce to 25% exposure
VIX_DEFCON_1 = 50  # Kill Switch threshold
