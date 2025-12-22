"""Contract Liabilities DTO"""

from typing import TypedDict


class ContractLiabilitiesDTO(TypedDict):
    """Contract liabilities (Specialized for Electronics/Construction/Equipment stocks)"""

    symbol: str
    current_value: float  # Current Contract Liabilities
    previous_value: float  # Previous Contract Liabilities
    qoq_change: float  # QoQ Growth Rate
    revenue_ratio: float  # Contract Liabilities / Revenue Ratio
    is_growing: bool  # QoQ > 0
