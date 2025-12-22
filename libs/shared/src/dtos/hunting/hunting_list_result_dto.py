"""Hunting List Result DTO"""

from typing import TypedDict

from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


class HuntingListResultDTO(TypedDict, total=False):
    """Hunting List Generation Result"""

    status: str  # success, failed
    market: str  # tw, us
    targets: list[ScanResultRowDTO]
    total_scanned: int
    timestamp: str
