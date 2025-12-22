"""Weather DTO

Weather Data Result
"""

from typing import TypedDict


class LiquidityQuadrantDTO(TypedDict):
    """Liquidity Quadrant"""

    name: str
    emoji: str
    m2_yoy: float
    fed_trend: str


class WeatherDTO(TypedDict):
    """Weather Data Result"""

    vix: float
    vix_tier: str
    vix_emoji: str
    defcon_level: int
    defcon_emoji: str
    gli_z: float
    kelly_factor: float
    overall_signal: str
    overall_action: str
    hurst: float
    hmm_state: int
    bull_prob: float
    pca_stability: float
    regime: str
    liquidity_quadrant: LiquidityQuadrantDTO
    cvar_95: float
    var_95: float
    tail_risk: str
