"""Stock Diagnosis DTO

Stock Diagnosis Result
"""

from typing import TypedDict


class StockDiagnosisDTO(TypedDict):
    """Stock Diagnosis Result"""

    symbol: str
    health_status: str
    issues: list[str]
    recommendations: list[str]
