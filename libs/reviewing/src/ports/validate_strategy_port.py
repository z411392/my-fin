"""驗證策略績效 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.reviewing.strategy_validation_result_dto import (
    StrategyValidationResultDTO,
)


class ValidateStrategyPort(Protocol):
    """驗證策略績效

    CLI Entry: fin validate
    """

    def execute(
        self, strategy: str = "default", days: int = 252, simulate: bool = False
    ) -> StrategyValidationResultDTO:
        """驗證策略績效是否來自技能"""
        ...
