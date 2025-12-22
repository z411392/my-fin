"""Full Scan Result DTO"""

from typing import TypedDict

from libs.shared.src.dtos.scan_result.market_scan_result_dto import MarketScanResultDTO
from libs.shared.src.dtos.scan_result.recommendation_dto import RecommendationDTO


class ScanResultDTO(TypedDict):
    """Full Scan Result"""

    date: str  # YYYY-MM-DD
    timestamp: str  # ISO 8601
    markets: dict[str, MarketScanResultDTO]  # {"tw": ..., "us": ...}
    recommendations: list[RecommendationDTO]
