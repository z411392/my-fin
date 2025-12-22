"""Diagnosis Result DTO"""

from typing import TypedDict


class DiagnosisResultDTO(TypedDict):
    """Diagnosis Result"""

    symbol: str
    name: str
    price: float
    roe: float
    pe_ratio: float
    revenue_growth: float
    fundamental_grade: str  # A, B, C, D, F
    advisor_consensus: str  # Aggressive, Diverged, Defensive
    verdict: str  # HOLD, OBSERVE, REDUCE
    rationale: str
