"""Alert Level"""

from enum import Enum


class AlertLevel(Enum):
    """Alert Level"""

    INFO = "INFO"
    WARNING = "WARNING"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"
