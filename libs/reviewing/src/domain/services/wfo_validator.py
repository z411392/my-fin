"""WFO Validator

Corresponds to algorithms.md §3.2
Walk-Forward Optimization rolling validation
"""

import numpy as np


def walk_forward_optimization(
    returns: np.ndarray,
    in_sample_pct: float = 0.7,
    n_splits: int = 5,
) -> tuple[np.ndarray, bool]:
    """
    Rolling OOS validation

    Args:
        returns: Strategy return series
        in_sample_pct: In-sample ratio
        n_splits: Number of splits

    Returns:
        tuple: (OOS equity curve, is monotonically increasing)
    """
    if len(returns) < n_splits * 2:
        return np.array([]), False

    split_size = len(returns) // n_splits
    oos_returns = []

    for i in range(n_splits):
        start = i * split_size
        end = start + split_size

        # Split IS/OOS
        is_end = int(start + split_size * in_sample_pct)
        out_sample = returns[is_end:end]
        oos_returns.extend(out_sample)

    if not oos_returns:
        return np.array([]), False

    equity_curve = np.cumsum(oos_returns)

    # Check if monotonically increasing (allow minor drawdowns)
    is_generally_up = (
        equity_curve[-1] > equity_curve[0] if len(equity_curve) > 1 else False
    )

    # More strict: check drawdown magnitude
    max_drawdown = 0.0
    peak = equity_curve[0]
    for val in equity_curve:
        if val > peak:
            peak = val
        drawdown = (peak - val) / (abs(peak) + 1e-8)
        max_drawdown = max(max_drawdown, drawdown)

    is_monotonic = is_generally_up and max_drawdown < 0.2

    return equity_curve, is_monotonic


def probability_backtest_overfitting(
    in_sample_sharpes: np.ndarray,
    out_sample_sharpes: np.ndarray,
) -> float:
    """
    Calculate Probability of Backtest Overfitting (PBO)

    Bailey et al. (2015)

    Args:
        in_sample_sharpes: IS Sharpe Ratios
        out_sample_sharpes: OOS Sharpe Ratios

    Returns:
        float: PBO (0-1)
    """
    if len(in_sample_sharpes) == 0 or len(out_sample_sharpes) == 0:
        return 1.0

    if len(in_sample_sharpes) != len(out_sample_sharpes):
        return 1.0

    n = len(in_sample_sharpes)

    # Calculate rank
    oos_rank = np.argsort(np.argsort(-out_sample_sharpes))

    # Best IS strategy's OOS rank
    best_is_idx = np.argmax(in_sample_sharpes)
    best_is_oos_rank = oos_rank[best_is_idx]

    # PBO = P(OOS rank > median)
    pbo = best_is_oos_rank / n
    return float(pbo)


def interpret_wfo_result(is_monotonic: bool, pbo: float) -> tuple[str, str]:
    """Interpret WFO result"""
    if is_monotonic and pbo < 0.3:
        return "Robust", "Strategy effective, can increase allocation"
    elif is_monotonic:
        return "Cautious", "Strategy effective but may be overfitted"
    elif pbo < 0.3:
        return "Unstable", "Poor OOS equity curve, reduce allocation"
    else:
        return "Invalid", "High overfitting risk, consider disabling"
