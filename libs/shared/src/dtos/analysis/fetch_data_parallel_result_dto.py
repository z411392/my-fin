"""Fetch Data Result DTO

Parallel data fetching result
"""

from typing import TypedDict, NotRequired, Any


class FetchDataParallelResultDTO(TypedDict, total=False):
    """Parallel data fetching result"""

    statementhub: dict[str, Any]
    """StatementDog Data"""

    momentum: dict[str, Any] | None
    """Momentum Data"""

    supply_chain: dict[str, Any] | None
    """Supply Chain Data"""

    sc_msg: NotRequired[str]
    """Supply Chain Message"""
