"""Supply Chain Opportunity DTO"""

from typing import TypedDict


class SupplyChainOpportunityDTO(TypedDict, total=False):
    """Supply Chain Opportunity"""

    tw_stock: str  # TW Stock Symbol
    us_stock: str  # US Stock Symbol
    beta: float  # Correlation Beta
    lead_lag: int  # Lead/Lag Days
    correlation: float  # Correlation Coefficient
    signal: str  # Trading Signal
