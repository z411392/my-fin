"""生成每日簡報 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.reporting.daily_digest_dto import DailyDigestDTO


class GenerateDailyDigestPort(Protocol):
    """生成每日簡報

    CLI Entry: fin digest
    """

    def execute(
        self, send_email: bool = False, simulate: bool = False
    ) -> DailyDigestDTO:
        """
        生成每日簡報

        Args:
            send_email: 是否發送 email
            simulate: 使用 Shioaji 模擬環境

        Returns:
            DailyDigestDTO: 簡報內容
        """
        ...
