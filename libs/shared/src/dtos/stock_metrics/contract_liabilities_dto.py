"""Contract Liabilities DTO"""

from typing import TypedDict


class ContractLiabilitiesDTO(TypedDict):
    """Contract Liabilities Trend Analysis Result"""

    symbol: str
    current_value: float  # Latest Contract Liabilities
    previous_value: float  # Last Year Same Period Contract Liabilities
    yoy: float  # YoY
    is_growing: bool  # Whether Growing
    latest_period: str  # Latest Period (e.g. "2024Q3")
    compare_period: str  # Comparison Period (e.g. "2023Q3")
