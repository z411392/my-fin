"""File Sync Status DTO

File synchronization status
"""

from typing import TypedDict, NotRequired


class FileSyncStatusDTO(TypedDict, total=False):
    """File synchronization status (Internal Use)"""

    file: str
    """Filename"""

    status: str
    """Status (updated/valid/error)"""

    years: NotRequired[list[int]]
    """Synced Years"""

    message: NotRequired[str]
    """Message"""

    error: NotRequired[str]
    """Error Message"""
