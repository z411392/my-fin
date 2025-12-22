"""Alert Message Data Structure"""

from typing import TypedDict


class AlertDTO(TypedDict, total=False):
    """Alert message

    Used for risk alerts, system notifications
    """

    level: str
    message: str
    timestamp: str
    source: str
