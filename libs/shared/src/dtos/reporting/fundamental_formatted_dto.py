"""Fundamental Formatted DTO

Formatted Fundamental Data Structure
"""

from typing import TypedDict, NotRequired


class FundamentalFormattedDTO(TypedDict, total=False):
    """Formatted Fundamental Data (Internal Use)"""

    # Revenue Momentum
    rev_yoy: NotRequired[float]
    rev_mom: NotRequired[float]

    # Profit Quality
    cfo_ratio: NotRequired[float]
    accrual_ratio: NotRequired[float]

    # Valuation
    pb: NotRequired[float]

    # F-Score
    f_score: NotRequired[int]

    # Margins
    gross_margin: NotRequired[float]
    operating_margin: NotRequired[float]
    net_margin: NotRequired[float]

    # Financial Ratios
    roe: NotRequired[float]
    roa: NotRequired[float]

    # Raw Data
    ttm_eps: NotRequired[float]
    total_debt: NotRequired[float]
    equity: NotRequired[float]
