"""Alpha/Beta Contribution DTO"""

from typing import TypedDict


class AlphaBetaContributionDTO(TypedDict):
    """Alpha/Beta Contribution Decomposition Result

    Corresponds to plan.md P0: Alpha/Beta Contribution Decomposition
    """

    alpha: float  # Daily Alpha (Intercept)
    beta: float  # Beta Coefficient

    alpha_contribution_pct: float  # Alpha Contribution Percentage
    beta_contribution_pct: float  # Beta Contribution Percentage

    total_return: float  # Total Return (%)
    alpha_return: float  # Alpha Return (%)
    beta_return: float  # Beta Return (%)

    r_squared: float  # Regression R-squared

    is_all_weather: bool  # Is All-Weather Candidate (Alpha > 50%)
