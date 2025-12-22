"""Historical Profit Loss Data Structure"""

from typing import TypedDict


class ProfitLossDTO(TypedDict):
    """Historical Profit Loss Record

    Used for Shioaji PnL query
    """

    symbol: str
    name: str
    quantity: int
    price: float
    cost: float
    pnl: float
    pnl_percent: float
    date: str
    cond: str  # Trade Condition (e.g. Cash/Margin)
