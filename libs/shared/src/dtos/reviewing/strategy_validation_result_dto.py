"""Strategy Validation Result DTO"""

from typing import TypedDict, NotRequired


class StrategyValidationResultDTO(TypedDict):
    """Strategy Validation Result

    Corresponds to ValidateStrategyPort.execute() return value
    """

    strategy: str
    """Strategy Name"""

    period_days: int
    """Length of Validation Period (Days)"""

    sharpe: float
    """Sharpe Ratio"""

    dsr: float
    """Deflated Sharpe Ratio"""

    psr: float
    """Probabilistic Sharpe Ratio"""

    skill_verdict: str
    """Skill Verdict (SKILL_DOMINATED/POSSIBLE_SKILL/INDETERMINATE/LUCK_DOMINATED)"""

    cpcv_passed: bool
    """Whether CPCV Passed"""

    is_simulated: NotRequired[bool]
    """Whether simulated mode"""

    recommendation: str
    """Action Recommendation"""
