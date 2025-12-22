"""Alpha Decay Checker

Corresponds to methodology-II.md §B
Checks Alpha decay from signal generation to execution
"""


def check_alpha_decay(
    initial_alpha: float,
    target_price: float,
    current_price: float,
    entry_price: float,
) -> tuple[str, float]:
    """
    Check Alpha decay level

    Args:
        initial_alpha: Initial expected Alpha (percentage, e.g., 0.05 = 5%)
        target_price: Target price
        current_price: Current price
        entry_price: Entry price

    Returns:
        tuple: (decision, remaining Alpha ratio)
    """
    if initial_alpha <= 0 or entry_price <= 0:
        return "ABORT", 0.0

    # Initial expected gain = entry price × expected return
    expected_gain = entry_price * initial_alpha

    # Remaining gain space = target price - current price
    remaining_gain = target_price - current_price

    # Remaining Alpha ratio = remaining gain space / initial expected gain
    if expected_gain <= 0:
        return "ABORT", 0.0

    remaining_ratio = remaining_gain / expected_gain

    if remaining_ratio >= 0.6:
        return "EXECUTE_FULL", remaining_ratio
    elif remaining_ratio >= 0.4:
        return "EXECUTE_HALF", remaining_ratio
    else:
        return "ABORT", remaining_ratio


def interpret_alpha_decay(decision: str, remaining: float) -> tuple[str, str]:
    """
    Interpret Alpha decay decision

    Args:
        decision: Decision code
        remaining: Remaining Alpha ratio

    Returns:
        tuple: (status, recommendation)
    """
    interpretations = {
        "EXECUTE_FULL": (
            "Sufficient",
            f"Remaining {remaining:.0%} Alpha, execute full position",
        ),
        "EXECUTE_HALF": (
            "Moderate",
            f"Remaining {remaining:.0%} Alpha, reduce position by 50%",
        ),
        "ABORT": ("Insufficient", f"Remaining {remaining:.0%} Alpha, abort trade"),
    }
    return interpretations.get(decision, ("Unknown", ""))


def calculate_alpha_half_life(
    alpha_history: list[float],
) -> tuple[float, str]:
    """
    Calculate Alpha half-life

    Args:
        alpha_history: Historical Alpha series (weekly)

    Returns:
        tuple: (half-life weeks, status)
    """
    if len(alpha_history) < 4:
        return float("inf"), "Insufficient data"

    # Calculate decay ratio
    first_half = sum(alpha_history[: len(alpha_history) // 2])
    second_half = sum(alpha_history[len(alpha_history) // 2 :])

    if first_half <= 0:
        return float("inf"), "No Alpha"

    decay_ratio = second_half / first_half

    if decay_ratio >= 1:
        return float("inf"), "Not decaying"
    elif decay_ratio > 0.5:
        half_life = len(alpha_history) / 2 * (-1 / (decay_ratio - 1))
        if half_life > 12:
            return half_life, "Healthy"
        elif half_life > 4:
            return half_life, "Warning"
        else:
            return half_life, "Danger"
    else:
        return 2.0, "Rapid decay"
