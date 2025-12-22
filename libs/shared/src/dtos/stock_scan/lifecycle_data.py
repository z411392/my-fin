"""Momentum Lifecycle Data DTO

Corresponds to stock_data_builder.build_lifecycle return structure
"""

from typing import TypedDict


class LifecycleData(TypedDict, total=False):
    """Momentum Lifecycle Data Structure"""

    signal_age_days: int | None  # Signal Age (Days)
    remaining_meat_ratio: float | None  # Remaining Profit Potential (0-1)
    residual_rsi: float | None  # Residual RSI (0-100)
    rsi_divergence: str | None  # RSI Divergence (none/bearish/bullish)
    frog_in_pan_id: float | None  # Frog-in-Pan Information Dispersion (ID)
    theoretical_price: float | None  # Theoretical Target Price
