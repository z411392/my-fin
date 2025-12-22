"""Consensus Result DTO

Consensus Calculation Result
"""

from typing import TypedDict


class ConsensusResultDTO(TypedDict):
    """Consensus Calculation Result (Internal Use)"""

    verdict: str
    """Verdict"""

    signal: str
    """Signal"""

    action: str
    """Recommended Action"""

    confidence: float
    """Confidence"""
