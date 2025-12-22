"""Quality Filter Calculator

Corresponds to algorithms.md §2.2
IVOL/MAX/ID/Amihud/Overnight Confirmation/RVOL Filters
"""

import numpy as np


# ========================================
# Alpha-Core V4.0: IVOL × F-Score 矩陣
# ========================================


def apply_ivol_fscore_matrix(
    ivol: float,
    ivol_percentile: float,
    f_score: int | None,
) -> tuple[bool, str, str]:
    """
    IVOL × F-Score Decision Matrix (Alpha-Core V4.0)

    High IVOL + High Quality = Oversold Opportunity
    High IVOL + Low Quality = Lottery Exclusion

    Args:
        ivol: IVOL absolute value
        ivol_percentile: IVOL percentile (0-100)
        f_score: F-Score (0-9) or None

    Returns:
        tuple: (passed, decision_type, reason)
            - passed: bool
            - decision_type: "OPPORTUNITY" | "STANDARD" | "DEFENSIVE" | "WATCH" | "REJECT"
            - reason: str
    """
    # Handle F-Score None case (US stocks or unavailable)
    if f_score is None:
        # Without F-Score, use traditional IVOL filter (exclude >80th)
        if ivol_percentile > 80:
            return False, "REJECT", "High IVOL (no F-Score to verify quality)"
        return True, "STANDARD", "No F-Score (using traditional filter)"

    # 高 IVOL (>80th percentile)
    if ivol_percentile > 80:
        if f_score >= 7:
            return True, "OPPORTUNITY", f"🎯 錯殺機會 (高 IVOL + F-Score {f_score})"
        elif f_score >= 5:
            return True, "WATCH", f"⚠️ 高 IVOL 但品質中等 (F-Score {f_score})"
        else:
            return False, "REJECT", f"❌ 彩票剔除 (高 IVOL + F-Score {f_score})"

    # 中 IVOL (40-80th)
    if ivol_percentile > 40:
        if f_score >= 5:
            return True, "STANDARD", f"✅ 標準候選 (F-Score {f_score})"
        else:
            return False, "REJECT", f"❌ 低品質剔除 (F-Score {f_score})"

    # 低 IVOL (<40th)
    if f_score >= 5:
        return True, "DEFENSIVE", f"🛡️ 防禦型持股 (低 IVOL + F-Score {f_score})"
    else:
        return False, "REJECT", f"❌ 低品質剔除 (F-Score {f_score})"


def get_ivol_percentile(ivol: float, ivol_history: list[float] | None = None) -> float:
    """
    Calculate IVOL percentile

    Args:
        ivol: Current IVOL value
        ivol_history: Historical IVOL values list, uses estimates if None

    Returns:
        Percentile (0-100)
    """
    if ivol_history and len(ivol_history) > 10:
        # Use real historical data to calculate percentile
        sorted_ivol = sorted(ivol_history)
        rank = sum(1 for v in sorted_ivol if v <= ivol)
        return (rank / len(sorted_ivol)) * 100

    # Without historical data, estimate using empirical thresholds
    # Based on typical stock IVOL distribution:
    # - Low vol: <2% daily volatility
    # - Medium vol: 2-4%
    # - High vol: >4%
    if ivol < 0.015:  # <1.5%
        return 20.0
    elif ivol < 0.02:  # 1.5-2%
        return 40.0
    elif ivol < 0.03:  # 2-3%
        return 60.0
    elif ivol < 0.04:  # 3-4%
        return 75.0
    else:  # >4%
        return 90.0


def calculate_ivol(residuals: np.ndarray, window: int = 252) -> float:
    """
    Calculate Idiosyncratic Volatility

    IVOL = 252-day standard deviation of residuals
    Exclusion rule: Exclude top 10% IVOL

    Args:
        residuals: Residual series
        window: Calculation window (default 252 days)

    Returns:
        float: IVOL value
    """
    if len(residuals) < window:
        window = len(residuals)

    if window <= 1:
        return 0.0

    return float(np.std(residuals[-window:], ddof=1))


def calculate_max_return(daily_returns: np.ndarray, window: int = 21) -> float:
    """
    Calculate maximum single-day gain in past N days

    Exclusion rule: Exclude top 10% MAX

    Args:
        daily_returns: Daily return series
        window: Calculation window (default 21 days)

    Returns:
        float: MAX value
    """
    if len(daily_returns) < window:
        window = len(daily_returns)

    if window == 0:
        return 0.0

    return float(np.max(daily_returns[-window:]))


def calculate_information_discreteness(
    daily_returns: np.ndarray, window: int = 252
) -> float:
    """
    Calculate Information Discreteness (FIP - Frog-in-the-Pan)

    Da et al. (2014)
    ID < 0: Continuous small gains (high quality, institutional driven)
    ID > 0: Discrete large gains (low quality, retail chasing)
    Exclusion rule: Exclude top 20% with ID > 0

    Args:
        daily_returns: Daily return series
        window: Calculation window (default 252 days)

    Returns:
        float: ID value (-1 to +1)
    """
    if len(daily_returns) < window:
        window = len(daily_returns)

    if window == 0:
        return 0.0

    returns = daily_returns[-window:]
    cumulative = np.sum(returns)
    pret = np.sign(cumulative)

    pct_neg = np.sum(returns < 0) / len(returns)
    pct_pos = np.sum(returns > 0) / len(returns)

    return float(pret * (pct_neg - pct_pos))


def calculate_amihud_illiq(
    daily_returns: np.ndarray, volumes: np.ndarray, window: int = 21
) -> float:
    """
    Calculate Amihud (2002) Illiquidity Indicator

    ILLIQ = Avg(|R| / Volume)
    Exclusion rule: Exclude top 10% Amihud

    Args:
        daily_returns: Daily return series
        volumes: Volume series
        window: Calculation window (default 21 days)

    Returns:
        float: Amihud ILLIQ value
    """
    if len(daily_returns) < window:
        window = len(daily_returns)

    if window == 0 or len(volumes) < window:
        return 0.0

    returns = daily_returns[-window:]
    vols = volumes[-window:]

    # Avoid division by zero
    illiq_values = np.abs(returns) / (vols + 1e-8)
    return float(np.mean(illiq_values))


def calculate_overnight_confirmation(
    open_prices: np.ndarray, close_prices: np.ndarray
) -> tuple[float, float, bool]:
    """
    Calculate Overnight Confirmation (Lou et al., 2019)

    Returns:
        tuple: (overnight_return, intraday_return, should_exclude)
    """
    if len(open_prices) < 1 or len(close_prices) < 2:
        return 0.0, 0.0, False

    overnight = open_prices[-1] / close_prices[-2] - 1
    intraday = close_prices[-1] / open_prices[-1] - 1

    # Exclusion condition: Intraday gain + Overnight drop = Retail chasing
    should_exclude = (intraday > 0) and (overnight <= 0)

    return float(overnight), float(intraday), should_exclude


def calculate_rvol_climax(
    volumes: np.ndarray,
    close_prices: np.ndarray,
    high_prices: np.ndarray,
    open_prices: np.ndarray,
    window: int = 20,
) -> tuple[float, bool]:
    """
    Calculate Relative Volume + Distribution Pattern Detection

    Args:
        volumes: Volume series
        close_prices: Close price series
        high_prices: High price series
        open_prices: Open price series
        window: Calculation window

    Returns:
        tuple: (RVOL Z-Score, should_exclude)
    """
    if len(volumes) < window:
        return 0.0, False

    slice_data = volumes[-window:-1]
    if len(slice_data) <= 1:
        return 0.0, False

    avg_vol = np.mean(slice_data)
    std_vol = np.std(slice_data, ddof=0)

    if std_vol == 0:
        rvol = 0.0
    else:
        rvol = (volumes[-1] - avg_vol) / (std_vol + 1e-8)

    # Upper shadow ratio
    body = abs(close_prices[-1] - open_prices[-1])
    upper_shadow = high_prices[-1] - max(close_prices[-1], open_prices[-1])

    if body == 0:
        shadow_ratio = float("inf")
    else:
        shadow_ratio = upper_shadow / body

    # Exclusion condition: Extreme volume + Long upper shadow
    should_exclude = (rvol > 5) and (shadow_ratio > 2)

    return float(rvol), should_exclude


class QualityFilterResult:
    """Quality Filter Result"""

    def __init__(
        self,
        ivol_pass: bool,
        max_pass: bool,
        id_pass: bool,
        amihud_pass: bool,
        overnight_pass: bool,
        rvol_pass: bool,
    ):
        self.ivol_pass = ivol_pass
        self.max_pass = max_pass
        self.id_pass = id_pass
        self.amihud_pass = amihud_pass
        self.overnight_pass = overnight_pass
        self.rvol_pass = rvol_pass

    @property
    def all_passed(self) -> bool:
        """Whether all filters passed"""
        return all(
            [
                self.ivol_pass,
                self.max_pass,
                self.id_pass,
                self.amihud_pass,
                self.overnight_pass,
                self.rvol_pass,
            ]
        )

    @property
    def passed_count(self) -> int:
        """Number of filters passed"""
        return sum(
            [
                self.ivol_pass,
                self.max_pass,
                self.id_pass,
                self.amihud_pass,
                self.overnight_pass,
                self.rvol_pass,
            ]
        )


def is_value_trap(
    pe_ratio: float | None,
    pe_percentile: float | None,
    accrual_ratio: float | None,
    accrual_threshold: float = 0.05,
) -> tuple[bool, str]:
    """
    Value Trap Filter (Alpha-Core V4.0)

    Exclusion rule: PE < 5th percentile + High accruals (> 5%)
    These stocks appear cheap but have deteriorating financial quality

    Args:
        pe_ratio: P/E ratio
        pe_percentile: PE percentile (0-100)
        accrual_ratio: Accrual ratio (Total Accruals / Total Assets)
        accrual_threshold: Accrual threshold (default 5%)

    Returns:
        tuple: (is_value_trap, reason)
    """
    # No data means not a value trap
    if pe_ratio is None or pe_percentile is None:
        return False, "PE data insufficient"

    if accrual_ratio is None:
        return False, "Accrual data insufficient"

    # Value trap condition: Extremely low PE + High accruals
    if pe_percentile < 5 and accrual_ratio > accrual_threshold:
        return True, f"⚠️ Value Trap (PE={pe_ratio:.1f}, Accrual={accrual_ratio:.1%})"

    return False, "✅ Passed value trap filter"
