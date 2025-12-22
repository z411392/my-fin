"""Trade Record DTO"""

from typing import TypedDict


class TradeRecordDTO(TypedDict, total=False):
    """Trade Record"""

    id: str  # Trade ID
    symbol: str  # Stock Symbol
    action: str  # BUY | SELL
    quantity: int  # Quantity
    price: float  # Price
    date: str  # Trade Date (YYYY-MM-DD)
    commission: float  # Commission
    note: str  # Note
