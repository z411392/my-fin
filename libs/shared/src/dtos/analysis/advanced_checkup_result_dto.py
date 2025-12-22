"""Advanced Checkup Result DTO

Advanced checkup result data structure
"""

from typing import TypedDict

from libs.shared.src.dtos.analysis.dimension_result_dto import DimensionResultDTO
from libs.shared.src.dtos.hunting.pricing_result_dto import PricingResultDTO
from libs.shared.src.dtos.hunting.scaling_result_dto import ScalingResultDTO


class AdvancedCheckupDetailsDTO(TypedDict, total=False):
    """Advanced checkup details"""

    alpha_decay: PricingResultDTO
    vol_scaling: ScalingResultDTO
    id_score: float
    meat_pct: float


class AdvancedCheckupResultDTO(TypedDict):
    """Advanced checkup result"""

    dimensions: list[DimensionResultDTO]
    must_exit: bool
    exit_reason: str
    details: AdvancedCheckupDetailsDTO
