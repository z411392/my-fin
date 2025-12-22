"""通知閘道 Fake Adapter"""

from libs.shared.src.dtos.event.notification_message_dto import NotificationMessageDTO
from libs.shared.src.dtos.risk_alert_dto import RiskAlertDTO
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort


class NotificationGatewayFakeAdapter(NotificationGatewayPort):
    """通知閘道 Fake"""

    def __init__(self) -> None:
        self._sent_alerts: list[RiskAlertDTO] = []
        self._sent_messages: list[NotificationMessageDTO] = []
        self._should_fail = False

    def set_should_fail(self, should_fail: bool) -> None:
        self._should_fail = should_fail

    def send_alert(self, alert: RiskAlertDTO) -> bool:
        if self._should_fail:
            return False
        self._sent_alerts.append(alert)
        return True

    def send_message(self, channel: str, message: str) -> bool:
        if self._should_fail:
            return False
        self._sent_messages.append(
            {"subject": channel, "body": message, "timestamp": ""}
        )
        return True

    def get_sent_alerts(self) -> list[RiskAlertDTO]:
        return self._sent_alerts

    def get_sent_messages(self) -> list[NotificationMessageDTO]:
        return self._sent_messages
