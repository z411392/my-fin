"""Momentum Lifecycle DTO

Encapsulates Momentum Lifecycle Dashboard Data
Corresponds to plan.md Phase 1.1
"""

from typing import TypedDict


class MomentumLifecycleDTO(TypedDict):
    """Momentum Lifecycle Data Structure"""

    signal_age: int  # Signal Age (days)
    lifecycle_stage: str  # young/mature/aging/exhausted
    lifecycle_emoji: str  # 🟢/🟡/🟠/🔴
    remaining_meat: float  # Remaining Profit Potential (0-1)
    meat_recommendation: str  # Aggressive Hold/Maintain/Reduce/Exit
    theoretical_price: float  # Theoretical Target Price
    expected_move: float  # Expected Move
    remaining_alpha: float  # Remaining Alpha Ratio
    alpha_signal: str  # EXECUTE/REDUCE/ABORT
    residual_rsi: float  # Residual RSI (0-100)
    rsi_divergence: str  # none/bearish/bullish
    yz_volatility: float  # Yang-Zhang Annualized Volatility
    vol_expansion: bool  # Whether Volatility Expanding
    vol_percentile: float  # Volatility Percentile (0-100)
