"""Profit Margins Data DTO"""

from typing import TypedDict


class ProfitMarginsDTO(TypedDict, total=False):
    """Profit Margins Data"""

    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
