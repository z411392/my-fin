"""Sync Result DTO

Sync operation result
"""

from typing import TypedDict


class SyncResultDTO(TypedDict, total=False):
    """Sync operation result (Internal Use)"""

    synced: bool
    """Whether sync completed"""

    message: str
    """Result message"""

    events_count: int
    """Events count"""
