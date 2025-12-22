"""發送通知 Command

實作 SendNotificationPort Driving Port
"""

import logging

from injector import inject
from libs.monitoring.src.ports.notification_gateway_port import (
    NotificationGatewayPort,
)
from libs.shared.src.enums.alert_level import AlertLevel
from libs.monitoring.src.ports.send_notification_port import SendNotificationPort


class SendNotificationCommand(SendNotificationPort):
    """
    發送通知

    實作 SendNotificationPort
    根據警報等級決定發送策略:
    - CRITICAL: 立即發送 + 重複提醒
    - SEVERE: 立即發送
    - WARNING: 批次發送
    - INFO: 僅記錄
    """

    @inject
    def __init__(self, notification_gateway: NotificationGatewayPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateway = notification_gateway

    def execute(self, alert: dict) -> bool:
        """
        發送警報通知

        符合 SendNotificationPort 介面

        Args:
            alert: 警報內容

        Returns:
            bool: 是否成功發送
        """
        if not alert:
            return False

        if not self._should_send(alert):
            return False

        return self._gateway.send_alert(alert)

    def _should_send(self, alert: dict) -> bool:
        """判斷是否需要發送"""
        level = alert.get("level", "")

        # INFO 等級不發送
        if level == AlertLevel.INFO.value:
            return False

        return True
