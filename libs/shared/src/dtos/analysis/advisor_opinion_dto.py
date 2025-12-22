"""Advisor Opinion Data Structure"""

from typing import TypedDict


class AdvisorOpinionDTO(TypedDict):
    """Advisor Opinion

    For multi-advisor consensus analysis
    """

    advisor: str
    opinion: str
    score: float
    reasoning: str
