"""Volatility Expansion Detector

Calculates volatility expansion related indicators:
- volatility_expansion_flag: Residual momentum new high AND volatility new high
- correlation_drift: Correlation rapidly rises from <0.3 to >0.7

Corresponds to plan.md P1 items
"""

import numpy as np


def calculate_volatility_expansion_flag(
    residual_momentum: np.ndarray,
    volatility: np.ndarray,
    lookback: int = 60,
) -> bool:
    """Calculate volatility expansion flag

    Residual momentum new high AND volatility new high = Trend acceleration signal

    Args:
        residual_momentum: Cumulative residual momentum series
        volatility: Volatility series (e.g., IVOL or Yang-Zhang)
        lookback: Lookback days (default 60)

    Returns:
        True if volatility expanding
    """
    if len(residual_momentum) < lookback or len(volatility) < lookback:
        return False

    mom_recent = residual_momentum[-lookback:]
    vol_recent = volatility[-lookback:]

    # Current value = last value in series
    mom_current = mom_recent[-1]
    vol_current = vol_recent[-1]

    # Check if new high
    mom_new_high = mom_current >= np.max(mom_recent)
    vol_new_high = vol_current >= np.max(vol_recent)

    return bool(mom_new_high and vol_new_high)


def detect_correlation_drift(
    correlation_series: np.ndarray,
    low_threshold: float = 0.3,
    high_threshold: float = 0.7,
    window: int = 20,
) -> bool:
    """Detect correlation drift

    Correlation coefficient rapidly rises from <0.3 to >0.7 = Alpha disappearing warning

    Args:
        correlation_series: Rolling correlation coefficient series
        low_threshold: Low threshold (default 0.3)
        high_threshold: High threshold (default 0.7)
        window: Detection window (default 20 days)

    Returns:
        True if correlation drift detected
    """
    if len(correlation_series) < window:
        return False

    recent = correlation_series[-window:]

    # Window start < low threshold, window end > high threshold
    start_low = recent[0] < low_threshold
    end_high = recent[-1] > high_threshold

    return bool(start_low and end_high)


def calculate_short_term_reversal(
    daily_returns: np.ndarray,
    lookback: int = 22,
) -> float:
    """Calculate short-term reversal factor (1 month cumulative return)

    Negative return may have mean reversion opportunity

    Args:
        daily_returns: Daily return series
        lookback: Lookback days (default 22 = 1 month)

    Returns:
        1 month cumulative return
    """
    if len(daily_returns) < lookback:
        return 0.0

    recent = daily_returns[-lookback:]
    cumulative = float(np.sum(recent))

    return round(cumulative, 6)
