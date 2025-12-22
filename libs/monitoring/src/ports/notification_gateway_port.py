"""通知閘道 Port"""

from typing import Protocol

from libs.shared.src.dtos.risk_alert_dto import RiskAlertDTO


class NotificationGatewayPort(Protocol):
    """通知閘道 Port (LINE/Telegram/Email)"""

    def send_alert(self, alert: RiskAlertDTO) -> bool:
        """發送警報通知

        Args:
            alert: 警報 DTO

        Returns:
            bool: 是否成功發送
        """
        ...

    def send_message(self, channel: str, message: str) -> bool:
        """發送純文字訊息

        Args:
            channel: 頻道 (email/line/telegram)
            message: 訊息內容

        Returns:
            bool: 是否成功發送
        """
        ...

    def send_markdown_email(self, subject: str, markdown_content: str) -> bool:
        """發送 Markdown 格式的 HTML Email

        Args:
            subject: Email 主旨
            markdown_content: Markdown 格式的內容

        Returns:
            bool: 是否成功發送
        """
        ...
