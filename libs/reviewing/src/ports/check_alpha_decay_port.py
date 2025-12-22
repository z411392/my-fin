"""檢查 Alpha 衰減 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.reviewing.alpha_decay_result_dto import AlphaDecayResultDTO


class CheckAlphaDecayPort(Protocol):
    """檢查 Alpha 衰減

    CLI Entry: fin alpha
    """

    def execute(
        self,
        symbol: str,
        entry_price: float,
        target_price: float,
        initial_alpha: float | None = None,
    ) -> AlphaDecayResultDTO:
        """檢查 Alpha 衰減

        Args:
            symbol: 股票代號
            entry_price: 進場價格
            target_price: 目標價格
            initial_alpha: 初始預期 Alpha（可選）
        """
        ...
