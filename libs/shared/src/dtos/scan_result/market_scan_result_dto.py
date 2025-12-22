"""Single Market Scan Result DTO"""

from typing import TypedDict

from libs.shared.src.dtos.hunting.candidate_stock_dto import CandidateStockDTO


class MarketScanResultDTO(TypedDict):
    """Single Market Scan Result"""

    market: str  # "tw" or "us"
    scanned: int  # Number of scanned targets
    qualified: int  # Number of qualified targets
    top_targets: list[CandidateStockDTO]  # Top N momentum targets
    bottom_targets: list[CandidateStockDTO]  # Bottom N momentum targets
