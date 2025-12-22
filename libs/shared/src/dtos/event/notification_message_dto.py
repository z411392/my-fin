"""Notification Message DTO"""

from typing import TypedDict


class NotificationMessageDTO(TypedDict):
    """Notification message

    Log records sent by notification gateway
    """

    subject: str
    body: str
    timestamp: str
