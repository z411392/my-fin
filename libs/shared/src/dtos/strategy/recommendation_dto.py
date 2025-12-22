"""Recommendation Data Structure"""

from typing import TypedDict


class RecommendationDTO(TypedDict):
    """Recommendation

    Used for action recommendation in Double Loop Learning
    """

    action: str
    reason: str
    priority: str
