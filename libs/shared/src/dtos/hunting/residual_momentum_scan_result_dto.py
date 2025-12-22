"""Residual Momentum Scan Result DTO"""

from typing import TypedDict, NotRequired

from libs.shared.src.dtos.hunting_target_dto import HuntingTargetDTO


class ResidualMomentumScanResultDTO(TypedDict):
    """Residual Momentum Scan Result

    Corresponds to ScanResidualMomentumPort.execute() return value
    """

    date: NotRequired[str]
    """Scan Date"""

    market: NotRequired[str]
    """Market"""

    scanned: NotRequired[int]
    """Number of scanned targets"""

    qualified: NotRequired[int]
    """Number of qualified targets"""

    targets: list[HuntingTargetDTO]
    """Scanned Targets"""

    errors: NotRequired[list[str]]
    """Error Messages (if any)"""
