"""F-Score DTO"""

from typing import TypedDict


class FScoreDTO(TypedDict):
    """Piotroski F-Score analysis result"""

    symbol: str
    total_score: int
    profitability_score: int
    leverage_liquidity_score: int
    efficiency_score: int
    # Profitability (4 pts)
    roa_positive: bool
    cfo_positive: bool
    roa_improving: bool
    accruals_valid: bool  # CFO > NI
    # Leverage, Liquidity and Source of Funds (3 pts)
    leverage_improving: bool  # Long-term Debt ratio decreasing
    liquidity_improving: bool  # Current Ratio increasing
    no_new_shares: bool
    # Operating Efficiency (2 pts)
    margin_improving: bool  # Gross Margin increasing
    turnover_improving: bool  # Asset Turnover increasing
    # Raw Data for reference (Optional)
    roa: float
    cfo: float
    net_income: float
    long_term_debt_ratio: float
    current_ratio: float
    gross_margin: float
    asset_turnover: float
