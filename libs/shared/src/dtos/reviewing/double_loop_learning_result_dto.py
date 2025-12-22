"""Double Loop Learning Result DTO

Double Loop Learning Result
"""

from typing import TypedDict

from libs.shared.src.dtos.strategy.trigger_condition_dto import TriggerConditionDTO
from libs.shared.src.dtos.strategy.hypothesis_dto import HypothesisDTO
from libs.shared.src.dtos.strategy.recommendation_dto import RecommendationDTO


class DoubleLoopLearningResultDTO(TypedDict):
    """Double Loop Learning Result"""

    timestamp: str
    """Timestamp"""

    strategy: str
    """Strategy Name"""

    reason: str
    """Trigger Reason"""

    trigger_conditions: list[TriggerConditionDTO]
    """Trigger Conditions"""

    hypothesis_review: list[HypothesisDTO]
    """Hypothesis Review"""

    recommendations: list[RecommendationDTO]
    """Recommendations"""

    learning_type: str
    """Learning Type"""

    status: str
    """Status"""
