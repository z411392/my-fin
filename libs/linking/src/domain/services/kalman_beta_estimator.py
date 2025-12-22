"""Kalman Beta Estimator

Corresponds to algorithms.md §2.5
Dynamic Beta estimation (simplified version)
"""

import numpy as np


def kalman_beta_simple(
    us_returns: np.ndarray,
    tw_returns: np.ndarray,
    process_noise: float = 0.01,
    observation_noise: float = 0.1,
) -> np.ndarray:
    """
    Simplified Kalman Filter Beta estimation

    No dependency on filterpy, uses basic Kalman equations

    Args:
        us_returns: US stock return series
        tw_returns: TW stock return series
        process_noise: Process noise Q
        observation_noise: Observation noise R

    Returns:
        np.ndarray: Dynamic Beta series
    """
    if len(us_returns) != len(tw_returns) or len(us_returns) == 0:
        return np.array([])

    n = len(us_returns)
    betas = np.zeros(n)

    # Initialize
    x = 1.0  # Initial Beta
    P = 1.0  # Initial covariance

    Q = process_noise
    R = observation_noise

    for t in range(n):
        # Prediction step (Random Walk Assumption for Beta)
        x_pred = x
        P_pred = P + Q

        # Update step
        # Observation model: tw_return = beta * us_return + noise
        # z (observation) = tw_returns[t]
        # H (observation matrix) = us_returns[t]

        z = tw_returns[t]
        h = us_returns[t]

        # Innovation (residual)
        innovation = z - h * x_pred

        # Innovation covariance
        S = h * P_pred * h + R

        # Kalman Gain
        K = P_pred * h / S

        # Update estimate
        x = x_pred + K * innovation
        P = (1 - K * h) * P_pred

        betas[t] = x

    return betas


def estimate_supply_chain_lag(
    us_returns: np.ndarray,
    tw_returns: np.ndarray,
    max_lag: int = 5,
) -> tuple[int, float]:
    """
    Estimate supply chain lead-lag days

    Args:
        us_returns: US stock return series
        tw_returns: TW stock return series
        max_lag: Maximum lag days

    Returns:
        tuple: (optimal lag days, correlation coefficient)
    """
    if len(us_returns) < max_lag + 10 or len(tw_returns) < max_lag + 10:
        return 0, 0.0

    best_corr = 0.0
    best_lag = 0

    for lag in range(max_lag + 1):
        if lag == 0:
            corr = np.corrcoef(us_returns, tw_returns)[0, 1]
        else:
            corr = np.corrcoef(us_returns[:-lag], tw_returns[lag:])[0, 1]

        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag

    return best_lag, float(best_corr)
