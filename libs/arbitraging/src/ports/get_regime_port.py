"""取得市場體制 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.market.regime_result_dto import RegimeResultDTO


class GetRegimePort(Protocol):
    """取得市場體制識別

    CLI Entry: fin regime
    """

    def execute(self) -> RegimeResultDTO:
        """
        取得當前市場體制

        Returns:
            RegimeResultDTO: 包含 regime, hurst, hmm_bull_prob 等
        """
        ...
