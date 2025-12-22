"""Pairs Trading Scan Result DTO"""

from typing import TypedDict, NotRequired

from libs.shared.src.dtos.hunting.pair_result_dto import PairResultDTO


class PairsScanResultDTO(TypedDict):
    """Pairs Trading Scan Result

    Corresponds to ScanPairsPort.execute() return value
    """

    sector: str
    """Sector"""

    market: NotRequired[str]
    """Market"""

    min_correlation: float
    """Minimum Correlation Threshold"""

    pairs: list[PairResultDTO]
    """Pairs List"""

    error: NotRequired[str]
    """Error Message (if any)"""
