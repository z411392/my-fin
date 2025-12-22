"""Alert DTO"""

from typing import TypedDict


class AlertDTO(TypedDict):
    """Alert data"""

    type: str  # RISK | OPPORTUNITY
    level: str  # INFO | WARNING | SEVERE | CRITICAL
    code: str  # Alert code
    message: str
    timestamp: str
