"""Returns Map DTO

Returns Data Structure
"""

from typing import TypedDict


class ReturnsMapDTO(TypedDict, total=False):
    """Returns Map (For Fake Adapter)"""

    portfolio: list[float]
    """Portfolio Returns"""

    benchmark: list[float]
    """Benchmark Returns"""

    dates: list[str]
    """Dates List"""
