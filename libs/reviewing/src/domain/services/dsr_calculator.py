"""DSR Calculator

Corresponds to algorithms.md §3.1
Deflated Sharpe Ratio - Bailey & de Prado (2014)
"""

import numpy as np
from scipy.stats import norm


def calculate_deflated_sharpe_ratio(
    sr: float,
    n_trials: int,
    n_observations: int,
    sr_std: float = 1.0,
) -> float:
    """
    Calculate Deflated Sharpe Ratio

    Corrects for multiple testing bias, determines if performance is skill or luck

    Args:
        sr: Actual Sharpe Ratio
        n_trials: Number of strategy trials
        n_observations: Number of observations
        sr_std: Sharpe Ratio standard deviation

    Returns:
        float: DSR (0-1)
    """
    if n_trials < 1 or n_observations < 1:
        return 0.0

    # Expected maximum SR (based on number of trials)
    euler_gamma = 0.5772156649

    ppf_1 = norm.ppf(1 - 1 / n_trials)
    ppf_2 = norm.ppf(1 - 1 / (n_trials * np.e))

    expected_max_sr = sr_std * ((1 - euler_gamma) * ppf_1 + euler_gamma * ppf_2)

    # DSR
    denominator = sr_std / np.sqrt(n_observations)
    if denominator == 0:
        return 0.0

    dsr = norm.cdf((sr - expected_max_sr) / denominator)
    return float(dsr)


def interpret_dsr(dsr: float) -> tuple[str, str]:
    """
    Interpret DSR value

    Returns:
        tuple: (judgment result, recommended action)
    """
    if dsr > 0.95:
        return "Skill Dominated", "Increase allocation"
    elif dsr > 0.75:
        return "Possible Skill", "Maintain allocation"
    elif dsr > 0.50:
        return "Indeterminate", "Reduce allocation"
    else:
        return "Luck Dominated", "Consider discontinuing"


def calculate_probabilistic_sharpe_ratio(
    sr: float,
    benchmark_sr: float,
    n_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Calculate Probabilistic Sharpe Ratio

    Args:
        sr: Actual Sharpe Ratio
        benchmark_sr: Benchmark Sharpe Ratio
        n_observations: Number of observations
        skewness: Return skewness
        kurtosis: Return kurtosis

    Returns:
        float: PSR (0-1)
    """
    if n_observations < 2:
        return 0.0

    # SR standard error
    se_sr = np.sqrt(
        (1 + 0.5 * sr**2 - skewness * sr + ((kurtosis - 3) / 4) * sr**2)
        / (n_observations - 1)
    )

    if se_sr == 0:
        return 0.0

    psr = norm.cdf((sr - benchmark_sr) / se_sr)
    return float(psr)
