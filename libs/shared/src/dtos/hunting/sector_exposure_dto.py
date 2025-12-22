"""Sector Exposure DTO

Sector Exposure Percentage
"""

from typing import TypedDict


class SectorExposureDTO(TypedDict, total=False):
    """Sector Exposure - Dynamic Keys

    Each key is a sector name, value is exposure percentage (0.0~100.0)
    Use total=False to allow arbitrary number of sectors
    """

    pass


# Type alias for dynamic sector exposure
SectorExposure = dict[str, float]
