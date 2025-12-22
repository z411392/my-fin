"""Pricing Data DTO

Corresponds to stock_data_builder.build_pricing return structure
"""

from typing import TypedDict


class PricingData(TypedDict, total=False):
    """Pricing Calculation Data Structure"""

    theo_price: float | None  # Theoretical Price
    remaining_alpha: float | None  # Remaining Alpha
    theoretical_price_deviation_pct: (
        float | None
    )  # Theoretical Price Deviation Percentage

    # OU Bands
    ou_upper_band: float | None  # OU Upper Band
    ou_lower_band: float | None  # OU Lower Band
