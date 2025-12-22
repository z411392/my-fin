"""Deep Analysis DTO

Deep Analysis Result
"""

from typing import TypedDict


class DeepAnalysisDTO(TypedDict):
    """Deep Analysis Result"""

    summary: str
    signals: list[str]
    risks: list[str]
    opportunities: list[str]
