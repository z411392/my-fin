"""Risk Alert DTO"""

from typing import TypedDict


class RiskAlertDTO(TypedDict):
    """Risk Alert"""

    code: str
    level: str  # INFO | WARNING | SEVERE | CRITICAL
    message: str
    current_value: float
    threshold: float
