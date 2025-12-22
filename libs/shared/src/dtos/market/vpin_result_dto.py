"""VPIN Calculation Result DTO"""

from typing import TypedDict, NotRequired


class VPINResultDTO(TypedDict):
    """VPIN calculation result"""

    vpin: float
    """VPIN value (0-1)"""

    level: NotRequired[str]
    """VPIN level (NORMAL/ELEVATED/CRITICAL)"""

    symbol: NotRequired[str]
    """Symbol"""

    timestamp: NotRequired[str]
    """Calculation timestamp"""
