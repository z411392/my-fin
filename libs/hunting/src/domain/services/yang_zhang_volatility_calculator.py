"""Yang-Zhang Volatility Calculator

Calculates advanced volatility estimator integrating overnight, open-to-close, Rogers-Satchell
Corresponds to diff.md §4.4 Residual Volatility Expansion
"""

import math
import numpy as np


def calculate_yang_zhang_volatility(
    open_prices: np.ndarray,
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    window: int = 20,
) -> float:
    """
    Calculate Yang-Zhang Volatility

    Formula: σ_YZ² = σ_O² + k·σ_C² + (1-k)·σ_RS²

    Where:
    - σ_O²: Overnight volatility (close-to-open)
    - σ_C²: Open-to-Close volatility
    - σ_RS²: Rogers-Satchell volatility
    - k = 0.34 / (1.34 + (n+1)/(n-1))

    Args:
        open_prices: Open price series
        high_prices: High price series
        low_prices: Low price series
        close_prices: Close price series
        window: Calculation window (default 20 days)

    Returns:
        float: Annualized Yang-Zhang volatility
    """
    n = min(len(open_prices), len(high_prices), len(low_prices), len(close_prices))

    if n < window + 1:
        return 0.0

    # Take recent window+1 days of data (need previous day's close)
    o = open_prices[-(window + 1) :]
    h = high_prices[-(window + 1) :]
    lo = low_prices[-(window + 1) :]
    c = close_prices[-(window + 1) :]

    # Log returns
    log_ho = np.log(h[1:] / o[1:])
    log_lo = np.log(lo[1:] / o[1:])
    log_co = np.log(c[1:] / o[1:])
    log_oc = np.log(o[1:] / c[:-1])  # Overnight

    # k coefficient
    k = 0.34 / (1.34 + (window + 1) / (window - 1))

    # Overnight 波動率
    overnight_mean = np.mean(log_oc)
    overnight_var = np.sum((log_oc - overnight_mean) ** 2) / (window - 1)

    # Open-to-Close 波動率
    oc_mean = np.mean(log_co)
    oc_var = np.sum((log_co - oc_mean) ** 2) / (window - 1)

    # Rogers-Satchell 波動率
    rs_var = np.mean(log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co))

    # Yang-Zhang 組合
    yz_var = overnight_var + k * oc_var + (1 - k) * rs_var

    # Ensure non-negative
    if yz_var < 0:
        yz_var = 0.0

    # Annualize (assuming 252 trading days)
    yz_annual = math.sqrt(yz_var * 252)

    return yz_annual


def check_volatility_expansion(
    current_vol: float,
    historical_vol: np.ndarray,
    threshold_percentile: float = 95,
) -> tuple[bool, float]:
    """
    Check volatility expansion alert

    Args:
        current_vol: Current volatility
        historical_vol: Historical volatility series
        threshold_percentile: Alert percentile (default 95)

    Returns:
        tuple: (is_expanding, current_percentile)
    """
    if len(historical_vol) < 10:
        return False, 50.0

    percentile = (np.sum(historical_vol <= current_vol) / len(historical_vol)) * 100

    is_expanding = percentile >= threshold_percentile

    return is_expanding, percentile


def calculate_volatility_ratio(
    current_vol: float,
    target_vol: float,
) -> tuple[float, float]:
    """
    Calculate volatility scaling weight

    Formula: W_t = W_target × (σ_target / σ_t)

    Args:
        current_vol: Current volatility
        target_vol: Target volatility

    Returns:
        tuple: (scaling_ratio, suggested_weight_adjustment)
    """
    if current_vol <= 0:
        return 1.0, 1.0

    ratio = target_vol / current_vol

    # Limit scaling range between 0.25 and 2.0
    ratio = max(0.25, min(2.0, ratio))

    return ratio, ratio


def interpret_volatility_state(
    yz_vol: float,
    percentile: float,
    is_expanding: bool,
) -> str:
    """
    Interpret volatility state

    Args:
        yz_vol: Yang-Zhang volatility
        percentile: Percentile
        is_expanding: Whether expanding

    Returns:
        str: Human-readable interpretation
    """
    vol_pct = yz_vol * 100

    if is_expanding:
        return f"⚠️ Vol Expansion | YZ-Vol: {vol_pct:.1f}% | Pctl: {percentile:.0f}% | Suggest reduce position"
    elif percentile >= 75:
        return f"🟡 Vol High | YZ-Vol: {vol_pct:.1f}% | Pctl: {percentile:.0f}% | Stay alert"
    elif percentile >= 25:
        return f"🟢 Vol Normal | YZ-Vol: {vol_pct:.1f}% | Pctl: {percentile:.0f}%"
    else:
        return f"🔵 Vol Low | YZ-Vol: {vol_pct:.1f}% | Pctl: {percentile:.0f}% | Calm environment"
