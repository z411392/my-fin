"""Momentum Lifecycle Calculator

Calculates momentum lifecycle related indicators:
- signal_age_days: Days since Z-Score first crossed +1.0
- remaining_meat_ratio: Remaining meat (Alpha decay)
- residual_rsi: RSI(14) of cumulative residual curve
- frog_in_pan_id: Information Discreteness (FIP effect)

Corresponds to plan.md P0 items
"""

import numpy as np


def calculate_signal_age(
    cumulative_residual: np.ndarray,
    threshold: float = 1.0,
) -> int:
    """Calculate signal age

    Days since Z-Score first crossed threshold

    Args:
        cumulative_residual: Cumulative residual series
        threshold: Breakthrough threshold (default +1.0 std)

    Returns:
        Signal age (days), -1 if never crossed
    """
    if len(cumulative_residual) < 2:
        return -1

    # Z-Score standardization
    mean = np.mean(cumulative_residual)
    std = np.std(cumulative_residual)
    if std == 0:
        return -1

    z_scores = (cumulative_residual - mean) / std

    # Find first breakthrough of threshold
    breakthrough_indices = np.where(z_scores > threshold)[0]
    if len(breakthrough_indices) == 0:
        return -1

    first_breakthrough = breakthrough_indices[0]
    signal_age = len(cumulative_residual) - first_breakthrough - 1

    return int(signal_age)


def calculate_remaining_meat(
    signal_age: int,
    half_life: float = 180.0,
) -> float:
    """Calculate remaining meat

    Based on Alpha decay model: exp(-age / half_life)

    Args:
        signal_age: Signal age (days)
        half_life: Half-life (default 180 days)

    Returns:
        Remaining meat (0-1), -1 if invalid
    """
    if signal_age < 0:
        return -1.0

    # Alpha decay formula
    remaining = np.exp(-signal_age / half_life)
    return float(round(remaining, 4))


def calculate_residual_rsi(
    cumulative_residual: np.ndarray,
    period: int = 14,
) -> float:
    """Calculate residual RSI

    Calculate RSI on cumulative residual curve

    Args:
        cumulative_residual: Cumulative residual series
        period: RSI period (default 14)

    Returns:
        Residual RSI (0-100), 50 if insufficient data
    """
    if len(cumulative_residual) < period + 1:
        return 50.0

    # Calculate daily changes
    deltas = np.diff(cumulative_residual)

    if len(deltas) < period:
        return 50.0

    # Take most recent period days
    recent_deltas = deltas[-period:]

    gains = np.where(recent_deltas > 0, recent_deltas, 0)
    losses = np.where(recent_deltas < 0, -recent_deltas, 0)

    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(round(rsi, 2))


def detect_rsi_divergence(
    price_series: np.ndarray,
    residual_rsi_series: np.ndarray,
    lookback: int = 20,
) -> str:
    """Detect RSI divergence

    Price new high but residual RSI not new high → bearish
    Price new low but residual RSI not new low → bullish

    Args:
        price_series: Price series
        residual_rsi_series: Residual RSI series
        lookback: Lookback days

    Returns:
        "bearish" / "bullish" / "none"
    """
    if len(price_series) < lookback or len(residual_rsi_series) < lookback:
        return "none"

    recent_price = price_series[-lookback:]
    recent_rsi = residual_rsi_series[-lookback:]

    # Price new high
    is_price_new_high = recent_price[-1] == np.max(recent_price)
    # RSI new high
    is_rsi_new_high = recent_rsi[-1] == np.max(recent_rsi)

    # Price new low
    is_price_new_low = recent_price[-1] == np.min(recent_price)
    # RSI new low
    is_rsi_new_low = recent_rsi[-1] == np.min(recent_rsi)

    if is_price_new_high and not is_rsi_new_high:
        return "bearish"
    if is_price_new_low and not is_rsi_new_low:
        return "bullish"

    return "none"


def calculate_frog_in_pan_id(
    daily_returns: np.ndarray,
    lookback: int = 60,
) -> float:
    """Calculate Information Discreteness (Frog-in-the-Pan)

    FIP = sign(PRET) × (%neg_days - %pos_days)

    Positive return but small daily gains (more negative days) → ID close to 0 or negative
    Positive return with continuous large gains (more positive days) → ID close to 1

    Args:
        daily_returns: Daily return series
        lookback: Lookback days (default 60)

    Returns:
        Information Discreteness (-1 to 1)
    """
    if len(daily_returns) < lookback:
        lookback = len(daily_returns)

    if lookback < 5:
        return 0.0

    recent = daily_returns[-lookback:]

    # Calculate cumulative return
    cumulative_return = np.sum(recent)
    sign_cumret = np.sign(cumulative_return)

    # Calculate positive/negative day ratios
    pos_days = np.sum(recent > 0) / lookback
    neg_days = np.sum(recent < 0) / lookback

    # FIP formula
    fip = sign_cumret * (neg_days - pos_days)

    return float(round(fip, 4))
