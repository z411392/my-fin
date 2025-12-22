"""Stock Pairs DTO

Stock Pairs Result
"""

from typing import TypedDict


class StockPairsDTO(TypedDict):
    """Stock Pairs Result"""

    symbol: str
    pair_symbol: str
    correlation: float
    spread_zscore: float
    half_life: float
    signal: str
