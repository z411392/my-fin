"""Get Monitor Data Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.market.monitor_data_dto import MonitorDataDTO


class GetMonitorPort(Protocol):
    """Get monitoring data

    CLI Entry: fin monitor
    """

    def execute(self) -> MonitorDataDTO:
        """
        Get real-time monitoring data

        Returns:
            MonitorDataDTO: Monitoring data
        """
        ...
