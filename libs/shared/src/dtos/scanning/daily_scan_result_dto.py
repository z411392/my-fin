"""Daily Scan Result DTO - For apps/scanning return"""

from typing import TypedDict

from libs.shared.src.dtos.hunting_target_dto import HuntingTargetDTO


class DailyScanResultDTO(TypedDict):
    """Daily Scan Result"""

    date: str  # YYYY-MM-DD
    market: str  # tw, tw_shioaji, us, us_full
    scanned: int  # Number of scanned targets
    qualified: int  # Number of qualified targets
    targets: list[HuntingTargetDTO]  # Scanned Targets
    pushed_count: int  # Number pushed to Sheets
    errors: list[str]  # Error messages (if any)
