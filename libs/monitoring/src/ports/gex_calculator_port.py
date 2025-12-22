"""GEX 計算器 Port"""

from typing import Protocol

from libs.shared.src.dtos.market.gex_result_dto import GEXResultDTO


class GEXCalculatorPort(Protocol):
    """GEX 計算器 Port"""

    def calculate(self, symbol: str) -> GEXResultDTO:
        """計算 Gamma Exposure"""
        ...
