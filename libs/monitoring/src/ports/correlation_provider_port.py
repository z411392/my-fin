"""
CorrelationProviderPort - Driven Port

實作者: CorrelationFakeAdapter
"""

from typing import Protocol

from libs.shared.src.dtos.market.correlation_matrix_dto import CorrelationMatrixDTO


class CorrelationProviderPort(Protocol):
    """Driven Port"""

    def calculate_matrix(self, symbols: list[str]) -> CorrelationMatrixDTO:
        """計算相關性矩陣"""
        ...
