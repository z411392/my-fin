"""Trade Record Data Structure"""

from typing import TypedDict


class TradeDealDTO(TypedDict):
    """Transaction Detail"""

    seq: str
    price: float
    quantity: int
    timestamp: int


class TradeDTO(TypedDict, total=False):
    """Trade Record

    Used for Shioaji trade query
    """

    order_id: str
    symbol: str
    name: str
    action: str
    price: float
    quantity: int
    status: str
    order_time: str | None
    deals: list[TradeDealDTO]
    total_filled: int
    avg_price: float
