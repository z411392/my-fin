"""Flattened Data DTO

Flattened Data Structure
"""

from typing import TypedDict, NotRequired


class FlattenedDataDTO(TypedDict, total=False):
    """Flattened CSV Format Data (Internal Use)"""

    SYMBOL: str
    """Stock Symbol"""

    UPDATED: NotRequired[str]
    """Updated Time"""

    # Market data
    PRICE: NotRequired[float]
    CHANGE_PCT: NotRequired[float]
    VOLUME: NotRequired[int]

    # Momentum
    MOMENTUM: NotRequired[float]
    IVOL: NotRequired[float]
    IVOL_PERCENTILE: NotRequired[float]

    # Signals
    SIGNAL: NotRequired[str]
    ENTRY_SIGNAL: NotRequired[str]

    # Extra fields use Any
    # Note: This DTO supports dynamic fields
