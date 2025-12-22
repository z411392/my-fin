"""Skill Metrics DTO

Skill Metrics Result
"""

from typing import TypedDict


class SkillMetricsDTO(TypedDict):
    """Skill Metrics Result"""

    dsr: float
    dsr_level: str
    psr: float
    deflated_sharpe: float
    skill_vs_luck: str
    note: str
