"""Frog in the Pan (FIP) Calculator

Calculates Information Discreteness (ID) indicator for momentum quality assessment.
Corresponds to diff.md §4.3 Information Discreteness

Theoretical basis:
"Frog in the Pan" theory states that momentum driven by continuous, small information
is more persistent than momentum driven by single, large information (Discrete Information).

ID = sign(PRET) * (%neg - %pos)
Where:
- PRET: Cumulative return over the period
- %neg: Percentage of negative return days
- %pos: Percentage of positive return days

Interpretation:
- ID < 0: Continuous momentum (high quality, frog gets boiled)
- ID > 0: Discrete momentum (low quality, prone to overreaction or attention)
"""

import numpy as np


def calculate_information_discreteness(
    daily_returns: np.ndarray,
) -> float:
    """
    Calculate Information Discreteness (ID)

    Args:
        daily_returns: Daily return series (percentage, e.g., 0.01 = 1%)

    Returns:
        float: ID value
    """
    if len(daily_returns) == 0:
        return 0.0

    # 1. Calculate cumulative return (PRET)
    # Use log return accumulation or simple return multiplication
    # Here we use simple summation as approximation (literature usually uses Cumulative Return)
    pret = np.sum(daily_returns)

    # 2. Calculate percentage of positive/negative return days
    # Ignore zero return days (usually rare)
    non_zero_returns = daily_returns[daily_returns != 0]

    if len(non_zero_returns) == 0:
        return 0.0

    n_pos = np.sum(non_zero_returns > 0)
    n_neg = np.sum(non_zero_returns < 0)
    total = len(non_zero_returns)

    pct_pos = n_pos / total
    pct_neg = n_neg / total

    # 3. Calculate ID
    # ID = sign(PRET) * (%neg - %pos)
    sign_pret = 1.0 if pret > 0 else (-1.0 if pret < 0 else 0.0)

    id_value = sign_pret * (pct_neg - pct_pos)

    return float(id_value)


def interpret_id_score(id_value: float) -> tuple[str, str]:
    """
    Interpret ID score

    Args:
        id_value: ID value

    Returns:
        tuple: (quality_label, description)
    """
    if id_value < -0.2:
        return "continuous", "🟢 High quality (continuous)"
    elif id_value <= 0:
        return "neutral", "🟡 Average (mixed)"
    else:
        # ID > 0
        return "discrete", "🔴 Low quality (discrete) - prone to reversal"


def check_id_filter(id_value: float, threshold: float = 0.0) -> bool:
    """
    ID filter check

    Args:
        id_value: ID value
        threshold: Exclusion threshold (default 0.0)

    Returns:
        bool: Whether passed filter (True = passed, False = excluded)
    """
    # We prefer momentum with ID < 0
    # If ID > threshold, exclude
    return id_value <= threshold
