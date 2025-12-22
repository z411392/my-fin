"""StatementDog Fundamental Data DTO

Corresponds to stock_data_builder.build_statementdog return structure
"""

from typing import TypedDict


class StatementDogData(TypedDict, total=False):
    """StatementDog Fundamental Data (Includes Computed Fields)"""

    # Revenue Momentum
    rev_yoy: float | None  # Revenue YoY (%)
    rev_mom: float | None  # Revenue MoM (%)

    # Earnings Quality
    cfo_ratio: float | None  # Operating Cash Flow Ratio
    accrual_ratio: float | None  # Accrual Ratio

    # Valuation Metrics
    pe: float | None  # P/E Ratio (Calc: close / ttm_eps)
    pb: float | None  # P/B Ratio
    f_score: int | None  # Piotroski F-Score

    # Profitability
    gross_margin: float | None  # Gross Margin (%)
    operating_margin: float | None  # Operating Margin (%)
    net_margin: float | None  # Net Margin (%)
    roe: float | None  # ROE (%)
    roa: float | None  # ROA (%)

    # Financial Structure
    debt_ratio: (
        float | None
    )  # Debt Ratio (%) (Calc: total_debt / (total_debt + equity))

    # Raw Data
    ttm_eps: float | None  # Trailing 12M EPS
    total_debt: float | None  # Total Debt
    equity: float | None  # Shareholders Equity
