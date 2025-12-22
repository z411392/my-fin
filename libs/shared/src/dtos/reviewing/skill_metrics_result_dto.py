"""Skill Metrics Result DTO"""

from typing import TypedDict


class SkillMetricsResultDTO(TypedDict):
    """Skill Metrics Result"""

    dsr: float  # Deflated Sharpe Ratio
    psr: float  # Probabilistic Sharpe Ratio (%)
    verdict: str  # Verdict Result
    confidence: str  # Confidence (High/Medium/Low)
    note: str  # Data Source Note
