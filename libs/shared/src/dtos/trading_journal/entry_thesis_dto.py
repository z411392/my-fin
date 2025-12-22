"""Entry Thesis DTO"""

from typing import TypedDict


class EntryThesisDTO(TypedDict, total=False):
    """Entry Thesis"""

    thesis: list[str]  # List of entry theses
    date: str  # Entry Date
    price: float  # Entry Price
