"""Weather Assessment Result DTO"""

from typing import TypedDict, NotRequired


class WeatherAssessmentDTO(TypedDict):
    """Weather Assessment Result"""

    # Core Metrics
    vix: float
    vix_tier: int | str
    signal: NotRequired[str]  # GREEN | YELLOW | RED (Legacy Compatibility)

    # DEFCON System
    defcon_level: NotRequired[int]  # 1-5
    defcon_emoji: NotRequired[str]
    permission: NotRequired[str]  # Permission Description
    action: NotRequired[str]  # Suggested Action

    # VIX Details
    vix_action: NotRequired[str]

    # VPIN
    vpin: NotRequired[float]

    # GLI Liquidity
    gli_z: NotRequired[float]
    gli_status: NotRequired[str]

    # Liquidity Quadrant (Legacy Compatibility)
    fed_trend: NotRequired[str]
    m2_yoy: NotRequired[float]
    liquidity_quadrant: NotRequired[str]

    # Market Data
    sp500_change: NotRequired[float]

    # Action Required
    requires_action: NotRequired[bool]
