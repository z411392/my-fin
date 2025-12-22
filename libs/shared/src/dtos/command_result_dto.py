"""Command Result DTO"""

from typing import TypedDict


class CommandResultDTO(TypedDict, total=False):
    """Generic command execution result

    Used for simple command execution results, all fields are optional
    """

    status: str  # success, failed, skipped
    message: str
    count: int
    path: str
    timestamp: str
    details: dict
