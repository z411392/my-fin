"""VPIN 計算器 Port"""

from typing import Protocol

from libs.shared.src.dtos.market.vpin_result_dto import VPINResultDTO


class VPINCalculatorPort(Protocol):
    """VPIN 計算器 Port"""

    def calculate(self, symbol: str) -> VPINResultDTO:
        """計算 VPIN"""
        ...
