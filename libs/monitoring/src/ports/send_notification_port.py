"""發送通知"""

from abc import abstractmethod
from typing import Protocol


class SendNotificationPort(Protocol):
    """發送通知"""

    @abstractmethod
    def execute(self, alert: dict) -> bool:
        """
        發送警報通知

        Args:
            alert: 警報內容

        Returns:
            bool: 是否成功發送
        """
        ...
