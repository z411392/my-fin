"""Correlation Matrix Result DTO"""

from typing import TypedDict


class CorrelationMatrixDTO(TypedDict):
    """Correlation Matrix Result

    Corresponds to CorrelationCalculatorPort.calculate_matrix() return value
    """

    symbols: list[str]
    """Symbols List"""

    matrix: list[list[float]]
    """Correlation Matrix"""

    average_correlation: float
    """Average Correlation"""
