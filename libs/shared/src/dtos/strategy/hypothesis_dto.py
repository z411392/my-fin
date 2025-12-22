"""Hypothesis Review Data Structure"""

from typing import TypedDict


class HypothesisDTO(TypedDict):
    """Hypothesis Review

    Used for hypothesis validation in Double Loop Learning
    """

    hypothesis: str
    result: str
    learning: str
