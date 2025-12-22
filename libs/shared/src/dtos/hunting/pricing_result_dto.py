"""Pricing Result DTO

Theoretical Price Calculation Result
"""

from typing import TypedDict


class PricingDetailsDTO(TypedDict, total=False):
    """Pricing Details"""

    systematic_component: float
    residual_component: float
    decay_lambda: float


class PricingResultDTO(TypedDict):
    """Theoretical Price Calculation Result"""

    target_price: float
    expected_move_pct: float
    model_type: str
    confidence: float
    details: PricingDetailsDTO
