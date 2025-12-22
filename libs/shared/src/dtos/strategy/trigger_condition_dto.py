"""Trigger Condition Data Structure"""

from typing import TypedDict


class TriggerConditionDTO(TypedDict):
    """Trigger Condition

    Used for condition evaluation in Double Loop Learning
    """

    condition: str
    triggered: bool
    value: float | None
