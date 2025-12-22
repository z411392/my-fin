"""Four Advisors DTO

Four Advisors Diagnosis Result
"""

from typing import TypedDict


class AdvisorVerdictDTO(TypedDict):
    """Single Advisor Verdict"""

    verdict: str
    reason: str


class FourAdvisorsDTO(TypedDict):
    """Four Advisors Diagnosis Result"""

    engineer: AdvisorVerdictDTO
    biologist: AdvisorVerdictDTO
    psychologist: AdvisorVerdictDTO
    strategist: AdvisorVerdictDTO
    consensus: str
    allocation: str
    attack_count: int
