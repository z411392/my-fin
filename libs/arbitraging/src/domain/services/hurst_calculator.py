"""Hurst Exponent Calculator

Corresponds to algorithms.md §1.3.1
R/S analysis to calculate Hurst exponent for market trend detection
"""

import numpy as np


def calculate_hurst_exponent(series: np.ndarray, max_lag: int = 100) -> float:
    """
    R/S analysis to calculate Hurst exponent

    H > 0.55: Trending market (momentum strategy)
    H < 0.45: Mean reversion (contrarian strategy)
    H ≈ 0.5: Random walk (no strategy advantage)

    Args:
        series: Price or return series
        max_lag: Maximum lag periods

    Returns:
        float: Hurst exponent (0-1)
    """
    if len(series) < max_lag:
        max_lag = len(series) // 2

    lags = range(2, max_lag)
    tau = []

    for lag in lags:
        # Calculate standard deviation at different lags
        std = np.std(np.subtract(series[lag:], series[:-lag]))
        if std > 0:
            tau.append(std)
        else:
            tau.append(1e-10)

    if len(tau) < 2:
        return 0.5  # Insufficient data, return random walk

    # Linear regression to estimate Hurst
    log_lags = np.log(list(lags)[: len(tau)])
    log_tau = np.log(tau)
    reg = np.polyfit(log_lags, log_tau, 1)

    return reg[0] * 2


def interpret_hurst(hurst: float) -> tuple[str, str]:
    """Interpret Hurst exponent"""
    if hurst > 0.55:
        return "Trending", "Residual momentum strategy"
    elif hurst < 0.45:
        return "Mean reversion", "Statistical arbitrage strategy"
    else:
        return "Random walk", "No strategy advantage"
