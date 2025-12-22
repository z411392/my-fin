"""Weekly Review DTO"""

from typing import TypedDict


class WeeklyReviewDTO(TypedDict):
    """Weekly Review DTO"""

    date: str  # Date
    dsr: float  # Deflated Sharpe Ratio
    psr: float  # Probabilistic Sharpe Ratio
    skill_judgment: str  # Skill judgment
    good_decision_rate: float  # Good decision rate (%)
    merril_phase: str  # Merrill clock phase
    recommended_asset: str  # Recommended asset
    recommendation: str  # Recommendation
