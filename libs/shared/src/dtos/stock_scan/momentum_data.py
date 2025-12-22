"""Momentum Data DTO

Corresponds to stock_data_builder.build_momentum return structure
"""

from typing import TypedDict


class MomentumData(TypedDict, total=False):
    """Momentum Scan Data Structure"""

    # Raw Momentum Values
    raw_momentum: float | None  # Residual Momentum Raw Value
    global_beta: float | None  # Global Beta
    local_beta: float | None  # Local Beta
    sector_beta: float | None  # Sector Beta
    ivol: float | None  # Idiosyncratic Volatility
    max_ret: float | None  # Max Daily Return

    # Quality Filter (Alpha-Core V4.0)
    id_score: float | None  # Information Dispersion Score
    id_pass: bool | None  # ID Filter Pass
    amihud_illiq: float | None  # Amihud Illiquidity
    overnight_return: float | None  # Overnight Return
    intraday_return: float | None  # Intraday Return
    overnight_pass: bool | None  # Overnight Filter Pass

    # EEMD Trend
    eemd_slope: float | None  # EEMD Slope
    eemd_days: int | None  # EEMD Trend Days
    eemd_confirmed: bool | None  # EEMD Trend Confirmed

    # Residual Source
    residual_source: str  # "ols" | "kalman" | "rolling"
