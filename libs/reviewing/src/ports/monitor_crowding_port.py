"""監控策略擁擠度 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.reviewing.crowding_result_dto import CrowdingResultDTO


class MonitorCrowdingPort(Protocol):
    """監控策略擁擠度

    CLI Entry: fin crowding
    """

    def execute(self, strategy: str = "residual_momentum") -> CrowdingResultDTO:
        """監控策略擁擠度"""
        ...
