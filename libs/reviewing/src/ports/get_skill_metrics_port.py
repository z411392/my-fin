"""
GetSkillMetricsPort - Driving Port

實作者: GetSkillMetricsQuery
"""

from typing import Protocol

from libs.shared.src.dtos.reviewing.skill_metrics_result_dto import (
    SkillMetricsResultDTO,
)


class GetSkillMetricsPort(Protocol):
    """Driving Port for GetSkillMetricsQuery"""

    def execute(
        self, strategy: str = "residual_momentum", days: int = 252
    ) -> SkillMetricsResultDTO:
        """執行主要操作"""
        ...
