"""Options Chain DTO"""

from typing import TypedDict, NotRequired


class OptionContractDTO(TypedDict):
    """Option Contract"""

    strike: float
    """Strike Price"""

    expiry: str
    """Expiry Date"""

    call_price: NotRequired[float]
    """Call Price"""

    put_price: NotRequired[float]
    """Put Price"""

    call_oi: NotRequired[int]
    """Call Open Interest"""

    put_oi: NotRequired[int]
    """Put Open Interest"""


class OptionsChainDTO(TypedDict):
    """Options Chain

    Corresponds to RealtimeMarketAdapterPort.get_options_chain() return value
    """

    symbol: str
    """Symbol"""

    contracts: list[OptionContractDTO]
    """Contracts List"""

    timestamp: NotRequired[str]
    """Timestamp"""
