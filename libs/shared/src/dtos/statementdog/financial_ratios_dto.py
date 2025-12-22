"""Financial Ratios Data DTO"""

from typing import TypedDict


class FinancialRatiosDTO(TypedDict, total=False):
    """Financial Ratios Data"""

    roe: float | None
    roa: float | None
    debt_ratio: float | None
    accrual_ratio: float | None
