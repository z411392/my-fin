"""
GetAdvisorConsensusPort - Driving Port

實作者: GetAdvisorConsensusQuery
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.advisor_consensus_result_dto import (
    AdvisorConsensusResultDTO,
)


class GetAdvisorConsensusPort(Protocol):
    """Driving Port for GetAdvisorConsensusQuery"""

    def execute(self, symbol: str) -> AdvisorConsensusResultDTO:
        """執行主要操作"""
        ...
