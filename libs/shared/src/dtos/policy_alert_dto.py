"""Policy Alert DTO

Alert structure returned from policy evaluation
"""

from typing import TypedDict


class PolicyAlertDTO(TypedDict, total=False):
    """Policy alert data"""

    code: str  # Alert code (e.g., VIX_TIER_2, VPIN_HIGH)
    level: str  # Alert level (INFO, WARNING, SEVERE, CRITICAL)
    message: str  # Alert message
    current_value: float  # Current value
    threshold: float  # Trigger threshold
    action: str  # Recommended action
