"""Tick Data Structure"""

from typing import TypedDict


class TickDTO(TypedDict, total=False):
    """Tick Data

    Used for VPIN calculation and Tick data processing
    """

    timestamp: str
    price: float
    quantity: int
    bid: float
    ask: float
