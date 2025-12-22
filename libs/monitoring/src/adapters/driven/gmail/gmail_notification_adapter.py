"""Gmail Notification Adapter

Implements NotificationGatewayPort
Uses Gmail SMTP to send alert notifications
Supports Markdown → HTML conversion
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown

import logging
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort


class GmailNotificationAdapter(NotificationGatewayPort):
    """Gmail Notification Adapter

    Requires environment variables:
    - GMAIL_USER: Gmail account
    - GMAIL_APP_PASSWORD: Gmail app password
    - GMAIL_RECIPIENTS: Recipients, comma-separated (defaults to GMAIL_USER)
    """

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # HTML Email 樣式
    HTML_STYLE = """
    <style>
        body {
            font-family: 'Segoe UI', 'Microsoft JhengHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .email-container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a2e;
            border-bottom: 3px solid #4a90d9;
            padding-bottom: 12px;
            margin-top: 0;
        }
        h2 {
            color: #16213e;
            border-left: 4px solid #4a90d9;
            padding-left: 12px;
            margin-top: 24px;
        }
        h3 {
            color: #0f3460;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
            font-size: 14px;
        }
        th {
            background-color: #4a90d9;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 10px 8px;
            border-bottom: 1px solid #e0e0e0;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e8f4fd;
        }
        blockquote {
            border-left: 4px solid #4a90d9;
            margin: 16px 0;
            padding: 12px 16px;
            background-color: #f0f7ff;
            color: #555;
            font-style: italic;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
        }
        pre {
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            color: inherit;
        }
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(to right, #e0e0e0, #4a90d9, #e0e0e0);
            margin: 24px 0;
        }
        ul, ol {
            padding-left: 24px;
        }
        li {
            margin: 8px 0;
        }
        strong {
            color: #1a1a2e;
        }
        .footer {
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #888;
            text-align: center;
        }
        /* Signal colors */
        .signal-green { color: #28a745; }
        .signal-yellow { color: #ffc107; }
        .signal-red { color: #dc3545; }
    </style>
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._user = os.environ.get("GMAIL_USER", "")
        self._password = os.environ.get("GMAIL_APP_PASSWORD", "")
        recipient_str = os.environ.get("GMAIL_RECIPIENTS", self._user)
        self._recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]

    def send_alert(self, alert: dict) -> bool:
        """Send alert notification"""
        if not self._user or not self._password:
            self._logger.warning(
                "⚠️ Gmail not configured (GMAIL_USER, GMAIL_APP_PASSWORD)"
            )
            return False

        level = alert.get("level", "INFO")
        code = alert.get("code", "ALERT")

        subject = f"[{level}] {code}"
        body = self._format_alert_body(alert)

        return self._send_email(subject, body)

    def send_message(self, channel: str, message: str) -> bool:
        """Send plain text message"""
        if not self._user or not self._password:
            return False

        return self._send_email(subject="MyFin Notification", body=message)

    def send_markdown_email(self, subject: str, markdown_content: str) -> bool:
        """Send HTML email from Markdown content

        Args:
            subject: Email subject
            markdown_content: Content in Markdown format

        Returns:
            Whether the email was sent successfully
        """
        if not self._user or not self._password:
            self._logger.warning(
                "⚠️ Gmail not configured (GMAIL_USER, GMAIL_APP_PASSWORD)"
            )
            return False

        # Convert Markdown to HTML
        html_body = self._markdown_to_html(markdown_content)

        return self._send_html_email(subject, html_body)

    def _markdown_to_html(self, md_content: str) -> str:
        """Convert Markdown to styled HTML"""
        # Use markdown package for conversion, enable table support
        html_content = markdown.markdown(
            md_content,
            extensions=["extra"],
        )

        # Compose complete HTML
        html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {self.HTML_STYLE}
</head>
<body>
    <div class="email-container">
        {html_content}
        <div class="footer">
            This email was auto-generated by MyFin | 
            <a href="https://github.com/z411392/my-fin">GitHub</a>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _format_alert_body(self, alert: dict) -> str:
        """Format alert content"""
        lines = [
            "🔔 MyFin Alert Notification",
            "",
            f"Level: {alert.get('level', 'N/A')}",
            f"Code: {alert.get('code', 'N/A')}",
            f"Message: {alert.get('message', 'N/A')}",
        ]

        if "current_value" in alert:
            lines.append(f"Current value: {alert['current_value']}")
        if "threshold" in alert:
            lines.append(f"Threshold: {alert['threshold']}")

        lines.extend(
            [
                "",
                "---",
                "This email was sent automatically by MyFin",
            ]
        )

        return "\n".join(lines)

    def _send_email(self, subject: str, body: str) -> bool:
        """Send plain text email"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self._user
            msg["To"] = ", ".join(self._recipients)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, self._recipients, msg.as_string())

            self._logger.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            self._logger.warning(f"Email send failed: {e}")
            return False

    def _send_html_email(self, subject: str, html_body: str) -> bool:
        """Send HTML format email"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self._user
            msg["To"] = ", ".join(self._recipients)
            msg["Subject"] = subject

            # Attach plain text version (fallback)
            plain_text = "This email contains HTML content. Please use an email client that supports HTML to view."
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))

            # Attach HTML version
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, self._recipients, msg.as_string())

            self._logger.info(f"HTML Email sent: {subject}")
            return True

        except Exception as e:
            self._logger.warning(f"Email send failed: {e}")
            return False
