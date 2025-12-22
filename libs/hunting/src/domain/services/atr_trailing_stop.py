"""ATR Trailing Stop Calculator

Alpha-Core V4.0: 3D Exit Mechanism — ATR Trailing Stop
Stop = Max_Price - 2 × ATR
"""

import numpy as np


def calculate_atr(
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    window: int = 14,
) -> float:
    """
    Calculate Average True Range

    TR = max(High - Low, |High - PrevClose|, |Low - PrevClose|)
    ATR = SMA(TR, window)

    Args:
        high_prices: High price series
        low_prices: Low price series
        close_prices: Close price series
        window: ATR window (default 14)

    Returns:
        ATR value
    """
    if len(high_prices) < window + 1:
        return 0.0

    # Calculate True Range
    tr_list = []
    for i in range(1, len(high_prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = close_prices[i - 1]

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)

    if len(tr_list) < window:
        return float(np.mean(tr_list)) if tr_list else 0.0

    # Use ATR of most recent window periods
    return float(np.mean(tr_list[-window:]))


def calculate_trailing_stop(
    max_price: float,
    atr: float,
    multiplier: float = 2.0,
) -> float:
    """
    Calculate ATR trailing stop price

    Stop = Max_Price - (multiplier × ATR)

    Args:
        max_price: Maximum price during holding period
        atr: ATR value
        multiplier: ATR multiplier (default 2.0)

    Returns:
        Stop price
    """
    return max_price - (multiplier * atr)


def should_trigger_trailing_stop(
    current_price: float,
    max_price: float,
    atr: float,
    multiplier: float = 2.0,
) -> tuple[bool, float, float]:
    """
    Determine if ATR trailing stop is triggered

    Args:
        current_price: Current price
        max_price: Maximum price during holding period
        atr: ATR value
        multiplier: ATR multiplier

    Returns:
        tuple: (triggered, stop_price, buffer_percentage)
    """
    stop_price = calculate_trailing_stop(max_price, atr, multiplier)
    buffer_pct = (
        ((current_price - stop_price) / current_price * 100) if current_price > 0 else 0
    )
    triggered = current_price <= stop_price

    return triggered, round(stop_price, 2), round(buffer_pct, 2)
