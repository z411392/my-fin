"""VPIN Level"""

from enum import Enum


class VPINLevel(Enum):
    """VPIN Level"""

    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
