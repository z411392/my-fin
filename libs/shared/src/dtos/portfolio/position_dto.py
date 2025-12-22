"""Position Data Structure"""

from typing import TypedDict


class PositionDTO(TypedDict, total=False):
    """Position Data

    Used for Shioaji position query and performance analysis
    """

    symbol: str
    name: str
    quantity: int
    cost: float
    current_price: float
    pnl: float
    pnl_percent: float
    stop_loss: float
    buffer_pct: float
    status: str
    status_text: str
