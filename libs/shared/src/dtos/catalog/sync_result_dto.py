"""Sync Result DTO"""

from typing import TypedDict, NotRequired


class SyncResultDTO(TypedDict):
    """Sync Result

    Corresponds to SyncCatalogPort.execute() return value
    """

    success: bool
    """Whether successful"""

    message: NotRequired[str]
    """Message"""

    synced_count: NotRequired[int]
    """Number of synced items"""

    skipped_count: NotRequired[int]
    """Number of skipped items"""

    from_cache: NotRequired[bool]
    """Whether from cache"""
