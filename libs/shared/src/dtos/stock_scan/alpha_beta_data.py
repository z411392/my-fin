"""Alpha/Beta Decomposition Data DTO

Corresponds to stock_data_builder.build_alpha_beta return structure
"""

from typing import TypedDict


class AlphaBetaData(TypedDict, total=False):
    """Alpha/Beta Contribution Decomposition Data Structure"""

    alpha: float | None  # Daily Alpha (Intercept)
    beta: float | None  # Beta Coefficient

    alpha_contribution_pct: float | None  # Alpha Contribution Percentage
    beta_contribution_pct: float | None  # Beta Contribution Percentage

    total_return: float | None  # Total Return (%)
    alpha_return: float | None  # Alpha Return (%)
    beta_return: float | None  # Beta Return (%)

    r_squared: float | None  # Regression R-squared
    is_all_weather: bool | None  # Whether All-Weather Candidate (Alpha > 50%)
