"""Risk Alert DTO

Risk Alert Data Structure
"""

from typing import TypedDict


class RiskAlertDTO(TypedDict, total=False):
    """Risk Alert (Corresponds to Policy return value)"""

    code: str
    """Alert code"""

    level: str
    """Alert level"""

    message: str
    """Alert message"""

    current_value: float
    """Current value"""

    threshold: float
    """Threshold"""

    gex_value: float
    """GEX value"""

    action: str
    """Recommended action"""
