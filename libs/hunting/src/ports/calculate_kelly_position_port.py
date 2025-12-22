"""計算凱利部位 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.portfolio.kelly_position_result_dto import (
    KellyPositionResultDTO,
)


class CalculateKellyPositionPort(Protocol):
    """計算凱利部位

    CLI Entry: fin position
    """

    def execute(
        self,
        symbol: str,
        capital: float = 1000000,
        win_rate: float = 0.55,
        avg_win: float = 0.08,
        avg_loss: float = 0.04,
    ) -> KellyPositionResultDTO:
        """
        計算凱利部位大小

        Returns:
            KellyPositionResultDTO: 包含 kelly_pct, position_size, shares 等
        """
        ...
