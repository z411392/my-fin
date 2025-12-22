"""Alpha Decay Check Result DTO"""

from typing import TypedDict


class AlphaDecayResultDTO(TypedDict):
    """Alpha Decay Check Result

    Corresponds to CheckAlphaDecayPort.execute() return value
    """

    symbol: str
    """Stock Symbol"""

    entry_price: float
    """Entry Price"""

    target_price: float
    """Target Price"""

    current_price: float
    """Current Price"""

    initial_alpha: float
    """Initial Alpha"""

    remaining: float
    """Remaining Alpha"""

    decision: str
    """Decision (EXECUTE/REDUCE/ABORT)"""

    status: str
    """Status Description"""

    advice: str
    """Advice"""
