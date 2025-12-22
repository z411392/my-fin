"""SendNotification 命令單元測試"""

from libs.monitoring.src.adapters.driven.memory.notification_gateway_fake_adapter import (
    NotificationGatewayFakeAdapter,
)
from libs.monitoring.src.application.commands.send_notification import (
    SendNotificationCommand,
)
from libs.shared.src.enums.alert_level import AlertLevel


class TestSendNotification:
    """發送通知測試"""

    def test_sends_critical_alert(self) -> None:
        """CRITICAL 警報應被發送"""
        gateway = NotificationGatewayFakeAdapter()
        command = SendNotificationCommand(notification_gateway=gateway)

        alert = {
            "code": "VIX_TIER3",
            "level": AlertLevel.CRITICAL.value,
            "message": "VIX 突破 35",
            "current_value": 40.0,
            "threshold": 35.0,
        }

        result = command.execute(alert)

        assert result is True
        assert len(gateway.get_sent_alerts()) == 1

    def test_sends_warning_alert(self) -> None:
        """WARNING 警報應被發送"""
        gateway = NotificationGatewayFakeAdapter()
        command = SendNotificationCommand(notification_gateway=gateway)

        alert = {
            "code": "VIX_TIER1",
            "level": AlertLevel.WARNING.value,
            "message": "VIX 突破 20",
            "current_value": 22.0,
            "threshold": 20.0,
        }

        result = command.execute(alert)

        assert result is True

    def test_does_not_send_info_alert(self) -> None:
        """INFO 警報不應被發送"""
        gateway = NotificationGatewayFakeAdapter()
        command = SendNotificationCommand(notification_gateway=gateway)

        alert = {
            "code": "DAILY_SUMMARY",
            "level": AlertLevel.INFO.value,
            "message": "每日摘要",
            "current_value": 0.0,
            "threshold": 0.0,
        }

        result = command.execute(alert)

        assert result is False
        assert len(gateway.get_sent_alerts()) == 0

    def test_handles_empty_alert(self) -> None:
        """空 dict 應返回 False"""
        gateway = NotificationGatewayFakeAdapter()
        command = SendNotificationCommand(notification_gateway=gateway)

        result = command.execute({})

        assert result is False

    def test_handles_gateway_failure(self) -> None:
        """網關失敗應返回 False"""
        gateway = NotificationGatewayFakeAdapter()
        gateway.set_should_fail(True)
        command = SendNotificationCommand(notification_gateway=gateway)

        alert = {
            "code": "VIX_TIER2",
            "level": AlertLevel.SEVERE.value,
            "message": "Test",
            "current_value": 30.0,
            "threshold": 25.0,
        }

        result = command.execute(alert)

        assert result is False

    def test_sends_multiple_alerts_sequentially(self) -> None:
        """多個警報應分別發送"""
        gateway = NotificationGatewayFakeAdapter()
        command = SendNotificationCommand(notification_gateway=gateway)

        alerts = [
            {
                "code": "VIX_TIER2",
                "level": AlertLevel.SEVERE.value,
                "message": "VIX",
                "current_value": 30.0,
                "threshold": 25.0,
            },
            {
                "code": "SP500_DROP",
                "level": AlertLevel.SEVERE.value,
                "message": "S&P500",
                "current_value": -3.5,
                "threshold": -3.0,
            },
        ]

        sent_count = sum(1 for alert in alerts if command.execute(alert))

        assert sent_count == 2
        assert len(gateway.get_sent_alerts()) == 2
