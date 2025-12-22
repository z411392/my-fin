"""Financial Info DTO"""

from typing import TypedDict, NotRequired


class FinancialInfoDTO(TypedDict):
    """Financial Info

    Corresponds to FinancialDataProviderPort.get_financial_info() return value
    """

    name: NotRequired[str]
    """Company Name"""

    price: NotRequired[float]
    """Current Price"""

    roe: NotRequired[float]
    """ROE"""

    pe_ratio: NotRequired[float]
    """P/E Ratio"""

    revenue_growth: NotRequired[float]
    """Revenue Growth Rate"""

    market_cap: NotRequired[float]
    """Market Cap"""


class AnalystRatingsDTO(TypedDict):
    """Analyst Ratings

    Corresponds to FinancialDataProviderPort.get_analyst_ratings() return value
    """

    strong_buy: NotRequired[int]
    """Strong Buy"""

    buy: NotRequired[int]
    """Buy"""

    hold: NotRequired[int]
    """Hold"""

    sell: NotRequired[int]
    """Sell"""

    strong_sell: NotRequired[int]
    """Strong Sell"""

    target_price: NotRequired[float]
    """Target Price"""
