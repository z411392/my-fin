"""Supply Chain Link DTO

Supply Chain Link Result
"""

from typing import TypedDict


class SupplyChainLinkDTO(TypedDict):
    """Supply Chain Link Result"""

    us_symbol: str
    tw_symbol: str
    beta: float
    correlation: float
    signal: str
