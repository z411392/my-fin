"""Pairs Trading Result DTO"""

from typing import TypedDict


class PairResultDTO(TypedDict):
    """Pair Result"""

    symbol_a: str
    symbol_b: str
    correlation: float
    half_life: float
    cointegration_pvalue: float
    spread_zscore: float
    status: str
