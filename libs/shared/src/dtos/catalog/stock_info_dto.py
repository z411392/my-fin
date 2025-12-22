"""Stock Info DTO"""

from typing import TypedDict


class StockInfoDTO(TypedDict):
    """Stock Basic Info"""

    code: str
    name: str
    market: str  # TSE, OTC, EMERGING, US, etc.
    industry: str
    currency: str
