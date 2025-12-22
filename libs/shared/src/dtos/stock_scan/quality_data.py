"""Quality Filter Data DTO

Corresponds to stock_data_builder.build_quality return structure
Alpha-Core V4.0 Quality Filter Indicators
"""

from typing import TypedDict


class QualityData(TypedDict, total=False):
    """Quality Filter Data Structure"""

    # Information Dispersion (FIP Effect): ID <= 0 means continuous small gains, high quality
    id_score: float | None
    id_pass: bool | None

    # Amihud Illiquidity: Higher value means worse liquidity
    amihud_illiq: float | None

    # Overnight Return Filter: ON/ID > 0.5 indicates institutional dominance
    overnight_return: float | None
    intraday_return: float | None
    overnight_pass: bool | None

    # EEMD Trend: slope > 0 and >= 3 days = Trend Confirmed
    eemd_slope: float | None
    eemd_days: int | None
    eemd_confirmed: bool | None

    # Mean Reversion Half Life
    half_life: float | None

    # Stock-Market Correlation (Alpha Decay Alert: rho > 0.7)
    correlation_20d: float | None
