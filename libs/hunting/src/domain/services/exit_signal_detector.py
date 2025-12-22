"""Exit Signal Detector

Calculates exit signal related indicators:
- stop_loss_triggered: 10% stop loss trigger
- beta_spike_alert: Beta spike alert
- beta_change_pct: Beta change rate

Corresponds to plan.md P0 items
"""

import numpy as np


def calculate_stop_loss_triggered(
    current_price: float,
    high_prices: np.ndarray,
    lookback: int = 20,
    threshold: float = 0.10,
) -> bool:
    """Calculate if 10% stop loss is triggered

    current_price < period_high × (1 - threshold)

    Args:
        current_price: Current price
        high_prices: High price series
        lookback: Lookback days (default 20 days = monthly)
        threshold: Stop loss ratio (default 10%)

    Returns:
        True if stop loss triggered
    """
    if current_price <= 0 or len(high_prices) < 1:
        return False

    period_high = np.max(high_prices[-lookback:])
    stop_price = period_high * (1 - threshold)

    return bool(current_price < stop_price)


def calculate_beta_change_pct(
    current_beta: float,
    prev_beta: float,
) -> float:
    """Calculate Beta change rate

    (current - prev) / abs(prev)

    Args:
        current_beta: Current Beta
        prev_beta: Previous Beta

    Returns:
        Beta change percentage, returns 0 if invalid
    """
    if prev_beta == 0 or np.isnan(prev_beta) or np.isnan(current_beta):
        return 0.0

    change_pct = (current_beta - prev_beta) / abs(prev_beta) * 100
    return float(round(change_pct, 2))


def calculate_beta_spike_alert(
    beta_change_pct: float,
    threshold: float = 50.0,
) -> bool:
    """Determine Beta spike alert

    |beta_change_pct| > threshold

    Args:
        beta_change_pct: Beta change percentage
        threshold: Alert threshold (default 50%)

    Returns:
        True if Beta spike
    """
    return bool(abs(beta_change_pct) > threshold)


def calculate_rolling_beta(
    stock_returns: np.ndarray,
    market_returns: np.ndarray,
    window: int = 60,
) -> np.ndarray:
    """Calculate rolling Beta

    Uses simple OLS regression

    Args:
        stock_returns: Individual stock return series
        market_returns: Market return series
        window: Rolling window (default 60 days)

    Returns:
        Rolling Beta series
    """
    n = len(stock_returns)
    if n < window or len(market_returns) < window:
        return np.array([])

    # Align lengths
    min_len = min(n, len(market_returns))
    stock = stock_returns[-min_len:]
    market = market_returns[-min_len:]

    betas = np.full(min_len, np.nan)

    for i in range(window - 1, min_len):
        y = stock[i - window + 1 : i + 1]
        x = market[i - window + 1 : i + 1]

        cov = np.cov(x, y)[0, 1]
        var_x = np.var(x)

        if var_x > 0:
            betas[i] = cov / var_x

    return betas


def calculate_atr_trailing_stop(
    current_price: float,
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    multiplier: float = 2.0,
    period: int = 14,
) -> float:
    """Calculate ATR trailing stop price

    stop_price = max_price - multiplier × ATR

    Args:
        current_price: Current price
        high_prices: High price series
        low_prices: Low price series
        close_prices: Close price series
        multiplier: ATR multiplier (default 2.0)
        period: ATR period (default 14)

    Returns:
        ATR trailing stop price, returns 0 if insufficient data
    """
    if (
        len(high_prices) < period + 1
        or len(low_prices) < period + 1
        or len(close_prices) < period + 1
    ):
        return 0.0

    # Calculate True Range
    tr_list = []
    for i in range(1, len(high_prices)):
        hl = high_prices[i] - low_prices[i]
        hc = abs(high_prices[i] - close_prices[i - 1])
        lc = abs(low_prices[i] - close_prices[i - 1])
        tr_list.append(max(hl, hc, lc))

    if len(tr_list) < period:
        return 0.0

    # ATR = Average TR of last period days
    atr = np.mean(tr_list[-period:])

    # Period high
    lookback = min(20, len(high_prices))
    max_price = np.max(high_prices[-lookback:])

    stop_price = max_price - multiplier * atr

    return float(round(stop_price, 2))
